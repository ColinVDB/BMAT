# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 13:16:48 2021

@author: ColinVDB & Maxence Wynen
"""


import os
import warnings
import subprocess
from pathlib import Path
from shutil import rmtree
import json
import shutil
from os.path import join as pjoin
from os.path import exists as pexists
import pandas as pd
from pydicom import dcmread
import logging
import sys
# from nipype.interfaces.dcm2nii import Dcm2niix

from tqdm.auto import tqdm
# from my_logging import setup_logging
import time



# =============================================================================
# BIDSHandler
# =============================================================================
class BIDSHandler:
    """
    """
    
    
    def __init__(self, root_dir, logger=None):
        """
        

        Parameters
        ----------
        root_dir : TYPE
            DESCRIPTION.
        dicom2niix_path : TYPE, optional
            DESCRIPTION. The default is "dcm2niix".
        logger : TYPE, optional
            DESCRIPTION. The default is None.

        Returns
        -------
        None.

        """
        self.root_dir = root_dir

        self.IGNORED_SERIES = ['3Plane_Loc_SSFSE',
                               'Ax T2 Propeller',
                               'AX REFORMAT',
                               'Opt_DTI_corr',
                               "COR REFORMAT"]
        
        # self.dcm2niix_converter = Dcm2niix()
        # self.dcm2niix_converter.inputs.out_filename = "\"%d_%p_%t_%s\""
        # self.dcm2niix_converter.inputs.compress = 'y'
        # self.dicom2niix_path = 'dcm2niix'

        all_directories = [x for x in next(os.walk(root_dir))[1]]
        all_subj_dir = []
        for d in all_directories:
            if d.find('sub-') == 0:
                all_subj_dir.append(d)
        self.number_of_subjects = len(all_subj_dir)
        
        # setup_logging('dicom2bids')
        self.logger = logging.getLogger('dicom2bids')
        self.logger.setLevel(logging.DEBUG)
        
        self.sequences_df = pd.read_csv('sequences.csv')
        self.sequences_df.fillna('', inplace=True)
        
        self.wrong_extensions = ['.jsn', '.bval', '.bvec', '.nii', '.gz', '.jpg']
        
        
    def addLoggerHandler(self, logger_handler, logger=logging):
        """
        

        Parameters
        ----------
        logger_handler : TYPE
            DESCRIPTION.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """
        self.logger.addHandler(logger_handler)
        

    def setDicom2niixPath(self, dcm2niix_path, logger=logging):
        """
        

        Parameters
        ----------
        dcm2niix_path : TYPE
            DESCRIPTION.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """
        self.dicom2niix_path = dcm2niix_path
        
        
    def update_number_of_subjects(self, logger=logging):
        """
        

        Parameters
        ----------
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """
        all_directories = [x for x in next(os.walk(self.root_dir))[1]]
        all_subj_dir = []
        for d in all_directories:
            if d.find('sub-') == 0:
                all_subj_dir.append(d)
        self.number_of_subjects = len(all_subj_dir)
        

    @staticmethod
    def rename(series, filenames, path, logger=logging):
        """
        

        Parameters
        ----------
        series : TYPE
            DESCRIPTION.
        filenames : TYPE
            DESCRIPTION.
        path : TYPE
            DESCRIPTION.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        if 'MPRAGE' in series or '3DT1' in series:
            if "ORIG" in series.upper():
                return ["run-orig_MPRAGE"]
            return ["MPRAGE"]
        if 'FLAIR' in series.upper(): # ORIG ???
            if "ORIG" in series.upper():
                return ["run-orig_FLAIR"]
            return ["FLAIR"]
        if 'phase' in series or ("SWI_EPI" in series and "_ph" in series):
            if "ORIG" in series.upper():
                return ["run-orig_acq-phase_T2star"]
            return ["acq-phase_T2star"]
        if '3D EPI' in series or "SWI_EPI" in series:
            if "ORIG" in series.upper():
                return ["run-orig_acq-mag_T2star"]
            return ["acq-mag_T2star"]
        if 'Opt_DTI' in series or 'DWI' in series:
            if len(filenames)>1:
                new_filenames = []
                for filename in filenames:
                    new_filenames.append('DWI')
                return new_filenames
            else:
                return ["DWI"]
        if "T1map" in series:
            return ["T1map"]
        if "DIR" in series:
            return ['DIR']
        if "T2opt" in series:
            return ['T2']
        if "T1W" in series and "gd" in series:
            return ['T1w_Gd']
        if "MP2RAGE" in series:
            if len(filenames)>1:
                new_filenames = []
                for filename in filenames:
                    try:
                        with open(f'{path}/{filename}.json') as json_file:
                            df = json.load(json_file)
                            new_filenames.append(f"inv-{df['EchoNumber']}_part-mag_MP2RAGE")
                    except:
                        pass
                return new_filenames
            else:
                return ['UNIT1']
            

    @staticmethod
    def bold(string):
        """
        

        Parameters
        ----------
        string : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        return "\033[1m" + string + "\033[0m"


    @staticmethod
    def mkdir_if_not_exists(dirpath, logger=logging):
        """
        

        Parameters
        ----------
        dirpath : TYPE
            DESCRIPTION.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """
        if not pexists(dirpath):
            os.mkdir(dirpath)
            

    def convert_all_dicoms(self, directory, convert=True, logger=logging):
        """
        Converts all dicom files of a particular patient into multiple
        compressed nifti (.nii.gz) files.

        Parameters
        ----------
        directory : <str>
            Path to patient's DICOM directory.
        dicom2niix_path : <str>
            ONLY FOR WINDOWS USERS. Path to dcm2niix.exe file.

        Returns
        -------
        all_sequences : <list> of <tuple>
            List of tuples (Path to specific dicom series directory,
                            Series description).

        """
        directory = pjoin(directory)
        logging.info("[INFO] Starting to convert ...")

        all_sequences = []
        for subdir, dirs, files in os.walk(directory):
            if len(dirs) !=0:#or len(files)< 10:
                continue
            logging.info(f"SUBDIR: {subdir}\tDIRS: {dirs}")#\nFILES: {files}\n")
            path = os.path.normpath(subdir)
            if convert:
                # self.dcm2niix_converter.inputs.source_dir = path
                # self.dcm2niix_converter.inputs.output_dir = directory
                # self.dcm2niix_converter.run()
                # subprocess.call([self.dicom2niix_path, '-f', "\"%d_%p_%t_%s\"",
                #                   "-p", "y", "-z", "y", '-o', directory, path])
                # subprocess.Popen(f'docker run --rm -v "{path}":/media -v "{directory}":/mnt xnat/dcm2niix dcm2niix -f \"%d_%p_%t_%s\" -p y -z y -o /mnt /media', shell=True).wait()
                # self.client.containers.run('xnat/dcm2niix', auto_remove=True, volumes={f'{path}':{'bind':'/media', 'mode':'ro'}, f'{directory}':{'bind':'/mnt', 'mode':'rw'}}, command=['dcm2niix -f \"%d_%p_%t_%s\" -p y -z y -o /mnt /media'])
                # subprocess.Popen(f'dcm2niix -f \"%d_%p_%t_%s\" -p y -z y -o {directory} {path}', shell=True).wait()
                subprocess.Popen(f'docker run --rm --privileged -v "{directory}":/home -v "{path}":/media colinvdb/bmat-dcm2niix dcm2niix -f \"%d_%p_%t_%s\" -p y -z y -o /home /media', shell=True).wait()
                
        for _,_,files in os.walk(directory):
            for file in files:
                if '.nii.gz' in file:
                    all_sequences.append((directory, file.replace('.nii.gz', '')))
        all_sequences = [(x[0].replace('\\', '/'),x[1]) for x in all_sequences]

        logging.info("[INFO] Converted dicom files to")
        logging.info(f"{BIDSHandler.bold(str(len(all_sequences)))} compressed nifti")
        return all_sequences
    

    @staticmethod
    def mkdirs_if_not_exist(root_dir, directories=["sourcedata",
                                                   "derivatives"], logger=logging):
        """
        

        Parameters
        ----------
        root_dir : TYPE
            DESCRIPTION.
        directories : TYPE, optional
            DESCRIPTION. The default is ["sourcedata",                                                   "derivatives"].
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """

        assert pexists(root_dir), f"Root directory {root_dir} does not exist."

        for dirname in directories:
            BIDSHandler.mkdir_if_not_exists(pjoin(root_dir, dirname))
    
    
    def make_directories(self, pat_id=None, session=None, logger=logging):
        # print('Make directories ???')
        """
        

        Parameters
        ----------
        pat_id : TYPE, optional
            DESCRIPTION. The default is None.
        session : TYPE, optional
            DESCRIPTION. The default is None.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        try:
            return self.make_directories_from(self.root_dir, pat_id, session)
        except Exception as e:
            print(e)
    
    
    @staticmethod
    def add_dataset_description_jsons(bids_dir, logger=logging):
        """
        

        Parameters
        ----------
        bids_dir : TYPE
            DESCRIPTION.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """
        if not pexists(pjoin(bids_dir, 'dataset_description.json')):
            dataset_description = { 
            	"Name": "dataset", 
            	"BIDSVersion":  "1.2.2", 
            }
            with open(pjoin(bids_dir, 'dataset_description.json'), 'w') as fp:
                json.dump(dataset_description, fp)
        
        else:
            with open(pjoin(bids_dir, 'dataset_description.json')) as dd:
                dataset_description = json.load(dd)

        for subdir,_,_ in os.walk(bids_dir):
            if subdir.endswith('derivatives'):
                for d in os.listdir(subdir):
                    if os.path.isdir(pjoin(subdir,d)):
                        dataset_description["Name"] = d
                        with open(pjoin(subdir, d, 'dataset_description.json'), 'w') as fp:
                            json.dump(dataset_description, fp)
                            
                            
    @staticmethod
    def update_authors_to_dataset_description(bids_dir, authors=[], logger=logging):
        """
        

        Parameters
        ----------
        bids_dir : TYPE
            DESCRIPTION.
        authors : TYPE, optional
            DESCRIPTION. The default is [].
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """
        logging.debug('Test to see if it is fucked !')
        with open(pjoin(bids_dir, 'dataset_description.json')) as dd:
            dataset_description = json.load(dd)
        dataset_description['Authors'] = authors
        with open(pjoin(bids_dir, 'dataset_description.json'), 'w') as dd:
            json.dump(dataset_description, dd)
            

    def get_dataset_description(self, logger=logging):
        """
        

        Parameters
        ----------
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        try:
            with open(pjoin(self.root_dir, 'dataset_description.json')) as dd:
                try:
                    dataset_description = json.load(dd)
                    return dataset_description
                except Exception:
                    return {}
        except FileNotFoundError:
            return {}
        
    
    @staticmethod
    def make_directories_from(bids_dir, pat_id=None, session=None, logger=logging):
        # print("WTF-make_directories_from !")
        """
        

        Parameters
        ----------
        bids_dir : TYPE
            DESCRIPTION.
        pat_id : TYPE, optional
            DESCRIPTION. The default is None.
        session : TYPE, optional
            DESCRIPTION. The default is None.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        pat_id : TYPE
            DESCRIPTION.
        session : TYPE
            DESCRIPTION.

        """

        BIDSHandler.mkdirs_if_not_exist(bids_dir, directories=["sourcedata", "derivatives"])

        define_pat_id = pat_id is None

        # Assign a database ID to the patient
        if define_pat_id:
            all_directories = [x for x in next(os.walk(bids_dir))[1]]
            all_subj_dir = []
            for d in all_directories:
                if d.find('sub-') == 0:
                    all_subj_dir.append(d)

            if all_subj_dir == []:
                pat_id = "001"
            else:
                subjects = [int(x.split('-')[1]) for x in all_subj_dir]
                pat_id = str((max(subjects) + 1)).zfill(3)

        subj_dir = pjoin(bids_dir,f"sub-{pat_id}")
        BIDSHandler.mkdir_if_not_exists(subj_dir)

        if session is None:
            all_directories = [x for x in next(os.walk(subj_dir))[1]]
            all_ses_dir = []
            for d in all_directories:
                if d.find('ses-') == 0:
                    all_ses_dir.append(d)
            if define_pat_id:
                session = "01"
            else:
                sessions = [int(x.split('-')[1]) for x in all_ses_dir]
                if len(sessions) == 0:
                    session = '01'
                else:
                    session = str(max(sessions) + 1).zfill(2)

        BIDSHandler.mkdir_if_not_exists(pjoin(bids_dir, 'sourcedata',
                                              f'sub-{pat_id}'))
        BIDSHandler.mkdir_if_not_exists(pjoin(bids_dir, 'sourcedata',
                                              f'sub-{pat_id}',
                                              f'ses-{session}'))

        BIDSHandler.mkdir_if_not_exists(pjoin(subj_dir, f'ses-{session}'))

        deriv = pjoin(bids_dir, 'derivatives')

        BIDSHandler.add_dataset_description_jsons(bids_dir)        
        
        if not pexists(pjoin(bids_dir, "README")):
            from shutil import copy as shcopy
            shcopy("readme_example", 
                   pjoin(bids_dir, "README"))
        
        # print("WTF-return make_directories_from")
        return pat_id, session
    

    @staticmethod
    def delete_if_exists(dirpath, logger=logging):
        """
        

        Parameters
        ----------
        dirpath : TYPE
            DESCRIPTION.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """
        if pexists(dirpath):
            rmtree(dirpath)
        else:
            logging.info("[Exception] Cannot remove directory that does not exists:")
            logging.info(f"\t{dirpath}")
            pass


    def delete_subject(self, pat_id, delete_sourcedata=False, logger=logging):
        """
        

        Parameters
        ----------
        pat_id : TYPE
            DESCRIPTION.
        delete_sourcedata : TYPE, optional
            DESCRIPTION. The default is False.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """
        patient_id = None
        if delete_sourcedata == False:
            try:
                participants = pd.read_csv(pjoin(self.root_dir, "participants.tsv"), sep='\t').to_dict()
            except FileNotFoundError: 
                logging.error('participants.tsv does not exists')
                return
            try:
                key_num = list(participants['participant_id'].values()).index(f'sub-{pat_id}')
            except ValueError:
                logging.error('sub-{pat_id} is not present in the database (participants.tsv)')
                return
            
            patient_id = participants['patient_id'][key_num]
            if patient_id == None:
                patient_id = participants['participant_name'][key_num]
            if patient_id == None:
                patient_id = pat_id
        
        bids_dir = self.root_dir
        subject_dirs = [dirpath for dirpath, subdirs, _ in os.walk(bids_dir)
                        if dirpath.endswith(f"sub-{pat_id}")]

        for s in subject_dirs:
            if "sourcedata" in s:
                if delete_sourcedata: 
                    rmtree(s)
                else:
                    dst = pjoin(s.replace(f'sub-{pat_id}',''), f'deleted_subjects', f'sub-{patient_id}')
                    shutil.copytree(s,dst)
                    rmtree(s)
            else:
                rmtree(s)
                
        self.modify_participants_tsv(old_sub=pat_id)
        

    def delete_session(self, pat_id, session, delete_sourcedata=False, logger=logging):
        """
        

        Parameters
        ----------
        pat_id : TYPE
            DESCRIPTION.
        session : TYPE
            DESCRIPTION.
        delete_sourcedata : TYPE, optional
            DESCRIPTION. The default is False.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """
        patient_id = None
        if delete_sourcedata == False:
            try:
                participants = pd.read_csv(pjoin(self.root_dir, "participants.tsv"), sep='\t').to_dict()
            except FileNotFoundError: 
                logging.error('participants.tsv does not exists')
                return
            try:
                key_num = list(participants['participant_id'].values()).index(f'sub-{pat_id}')
            except ValueError:
                logging.error('sub-{pat_id} is not present in the database (participants.tsv)')
                return
            
            patient_id = participants['patient_id'][key_num]
            if patient_id == None:
                patient_id = participants['participant_name'][key_num]
            if patient_id == None:
                patient_id = pat_id
                
        bids_dir = self.root_dir
        dirs = [dirpath for dirpath, subdirs, _ in os.walk(bids_dir)
                    if f"sub-{pat_id}" in dirpath and
                        dirpath.endswith(f"ses-{session}")]

        for s in dirs:
            if "sourcedata" in s:
                if delete_sourcedata: 
                    rmtree(s)
                else:
                    dst = pjoin(s.replace(f'ses-{session}',''), f'deleted_sessions', f'delses-{session}')
                    shutil.copytree(s,dst)
                    rmtree(s)
            else:
                rmtree(s)
                
        self.modify_participants_tsv(old_sub=pat_id, new_sub=pat_id, old_ses=session)
        

    def rename_and_move_nifti(self, dicom_series, pat_id, session='01', logger=logging):
        # print('WTF???')
        """
        

        Parameters
        ----------
        dicom_series : TYPE
            DESCRIPTION.
        pat_id : TYPE
            DESCRIPTION.
        session : TYPE, optional
            DESCRIPTION. The default is '01'.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """

        def move_all(path, filename, file_extensions, dest_dir, new_filename):
            """
            

            Parameters
            ----------
            path : TYPE
                DESCRIPTION.
            filename : TYPE
                DESCRIPTION.
            file_extensions : TYPE
                DESCRIPTION.
            dest_dir : TYPE
                DESCRIPTION.
            new_filename : TYPE
                DESCRIPTION.

            Returns
            -------
            None.

            """
            logging.info(filename)
            for file_extension in file_extensions:
                if pexists(pjoin(path, f"{filename}{file_extension}")):
                    if pexists(pjoin(dest_dir, f"{new_filename}{file_extension}")):
                        logging.info(f'File already existing in dest dir {pjoin(dest_dir, f"{new_filename}{file_extension}")}')
                        new_filename_ext = new_filename
                        while pexists(pjoin(dest_dir, f"{new_filename_ext}{file_extension}")):
                            new_filename_details = new_filename_ext.split('_')
                            if all(['run-' not in e for e in new_filename_details]):
                                new_filename_details.insert(len(new_filename_details)-1, 'run-2')
                                new_filename_ext = ''.join(e+'_' for e in new_filename_details)[:-1]
                            else:
                                run_index = ['run-' in e for e in new_filename_details].index(True)
                                run_value = new_filename_details[run_index]
                                run_ext = run_value.split('-')[1]
                                new_run_ext = f'run-{int(run_ext)+1}'
                                new_filename_details.remove(run_value)
                                new_filename_details.insert(run_index, new_run_ext)
                                new_filename_ext = ''.join(e+'_' for e in new_filename_details)[:-1]
                            if not pexists(pjoin(dest_dir, f"{new_filename_ext}{file_extension}")):
                                shutil.move(pjoin(path, f"{filename}{file_extension}"),
                                        pjoin(dest_dir, f"{new_filename_ext}{file_extension}"))
                                break
                        
                    else:
                        shutil.move(pjoin(path, f"{filename}{file_extension}"),
                            pjoin(dest_dir, f"{new_filename}{file_extension}"))
                        
        
        for path, filename in dicom_series:
            
            file_extensions = []
            for _,_,files in os.walk(path):
                for file in files:
                    if filename in file:
                        file_path, file_extension = os.path.splitext(file)
                        if file_extension == '.gz':
                            if '.nii' in file_path:
                                file_extensions.append('.nii.gz')
                                file_path.replace('.nii', '')
                        else:
                            file_extensions.append(file_extension)  
                            
            bids_sequence_name = {}
            

            for modality in self.sequences_df.get('modality'):
                if '+' in modality:
                    modalities = modality.split('+')
                else:
                    modalities = [modality]
                if all([mod in filename for mod in modalities]):
                    mod_sequences_df = self.sequences_df[self.sequences_df['modality'] == modality]
                    bids_sequence_name['modality_bids'] = list(mod_sequences_df.get('modality_bids'))[0]
                    bids_sequence_name['MRI_type'] = list(mod_sequences_df.get('MRI_type'))[0]

                    for key in mod_sequences_df.keys():
                        if key not in ['modality', 'modality_bids', 'MRI_type'] and 'bids' not in key:
                            i = 0
                            for k in mod_sequences_df.get(key):
                                if k in filename:
                                    if k != '':
                                        bids_sequence_name[f'{key}_bids'] = list(mod_sequences_df.get(f'{key}_bids'))[i]
                                        break
                                i = i+1
                    break
                                    
            if bids_sequence_name.get('MRI_type') != None and bids_sequence_name.get('MRI_type') != 'IGNORED':
                bids_filename = f'sub-{pat_id}_ses-{session}_'
                for key in bids_sequence_name.keys():
                    if key not in ['modality_bids', 'MRI_type']:
                        field = key.replace('_bids','')
                        label = bids_sequence_name[key]
                        try:
                            label = int(label)
                        except ValueError:
                            pass                                
                        bids_filename = bids_filename + f'{field}-{label}_'
                bids_filename = bids_filename + bids_sequence_name['modality_bids']
                BIDSHandler.mkdir_if_not_exists(pjoin(self.root_dir, f'sub-{pat_id}', f'ses-{session}', bids_sequence_name['MRI_type']))
                move_all(path, filename, file_extensions, pjoin(self.root_dir, f"sub-{pat_id}", f"ses-{session}", bids_sequence_name['MRI_type']), bids_filename)
            elif bids_sequence_name.get('MRI_type') == 'IGNORED':
                print('Remove', filename)
                for ext in file_extensions:
                    if pexists(pjoin(path,f'{filename}{ext}')):
                        os.remove(pjoin(path,f'{filename}{ext}'))
            else:
                bids_filename = f'sub-{pat_id}_ses-{session}_'
                for key in bids_sequence_name.keys():
                    if key not in ['modality_bids', 'MRI_type']:
                        field = key.replace('_bids','')
                        label = bids_sequence_name[key]
                        try:
                            label = int(label)
                        except ValueError:
                            pass                                
                        bids_filename = bids_filename + f'{field}-{label}_'
                bids_filename = bids_filename + filename
                BIDSHandler.mkdir_if_not_exists(pjoin(self.root_dir, f'sub-{pat_id}', f'ses-{session}', 'unrecognized_sequences'))
                move_all(path, filename, file_extensions, pjoin(self.root_dir, f"sub-{pat_id}", f"ses-{session}", 'unrecognized_sequences'), bids_filename)
                            
                                
    @staticmethod
    def delete_nii_json_in_dicomdir(dicom_series, logger=logging):
        """
        

        Parameters
        ----------
        dicom_series : TYPE
            DESCRIPTION.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """
        for path, series in dicom_series:
            for file in os.listdir(path):
                if file.endswith(".nii.gz") or file.endswith(".json"):
                    os.remove(pjoin(path, file))


    def rename_subject(self, old_id, new_id, logger=logging):
        """
        

        Parameters
        ----------
        old_id : TYPE
            DESCRIPTION.
        new_id : TYPE
            DESCRIPTION.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Raises
        ------
        FileExistsError
            DESCRIPTION.
        FileNotFoundError
            DESCRIPTION.

        Returns
        -------
        None.

        """
        bids_dir = self.root_dir
        # Replaces all paths with "sub-old_id" by the same path with "sub-new_id"
        if pexists(pjoin(bids_dir, f'sub-{new_id}')):
            msg = f"Subject {new_id} already exists in the database. "
            msg += "Delete the subject first or choose another subject id."
            logging.error(msg)
            raise FileExistsError(msg)
            
        if not pexists(pjoin(bids_dir, f'sub-{old_id}')):
            logging.error(f"Subject {old_id} is not in the database.")
            raise FileNotFoundError(f"Subject {old_id} is not in the database.")

        for dirpath, _, files in os.walk(bids_dir):

            if "sourcedata" in dirpath: continue

            for filename in files:
                if filename.startswith(f'sub-{old_id}'):
                    shutil.move(pjoin(dirpath, filename),
                                pjoin(dirpath, filename.replace(f"sub-{old_id}",
                                                                f"sub-{new_id}")))

        for dirpath, _, _ in os.walk(bids_dir):
            if dirpath.endswith(f"sub-{old_id}"):
                shutil.move(dirpath, dirpath.replace(f"sub-{old_id}",
                                                     f"sub-{new_id}"))
        
        self.modify_participants_tsv(old_sub=old_id, new_sub=new_id)
        

    def rename_session(self, subject, old_ses, new_ses, logger=logging):
        """
        

        Parameters
        ----------
        subject : TYPE
            DESCRIPTION.
        old_ses : TYPE
            DESCRIPTION.
        new_ses : TYPE
            DESCRIPTION.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Raises
        ------
        FileExistsError
            DESCRIPTION.
        FileNotFoundError
            DESCRIPTION.

        Returns
        -------
        None.

        """
        bids_dir = self.root_dir
        # Replaces all paths with "sub-old_id" by the same path with "sub-new_id"
        if pexists(pjoin(bids_dir, f'sub-{subject}',f'ses-{new_ses}')):
            msg = f"Session {new_ses} already exists for sub-{subject} in the database. "
            msg += "Delete the session for this subject first or choose another session."
            logging.error(msg)
            raise FileExistsError(msg)
    
        if not pexists(pjoin(bids_dir, f'sub-{subject}')):
            logging.error(f"Subject {old_ses} is not in the database.")
            raise FileNotFoundError(f"Subject {old_ses} is not in the database.")
            
        if not pexists(pjoin(bids_dir, f'sub-{subject}', f'ses-{old_ses}')):
            logging.error(f"Session {old_ses} for Subject {subject} is not in the database.")
            raise FileNotFoundError(f"Session {old_ses} for Subject {subject} is not in the database.")

        for dirpath, _, files in os.walk(bids_dir):

            if "sourcedata" in dirpath: continue

            for filename in files:
                if f'sub-{subject}' in dirpath and f'ses-{old_ses}' in dirpath:
                    shutil.move(pjoin(dirpath, filename),
                                pjoin(dirpath, filename.replace(f"ses-{old_ses}",
                                                                f"ses-{new_ses}")))

        for dirpath, _, _ in os.walk(bids_dir):
            if f'sub-{subject}' in dirpath and dirpath.endswith(f'ses-{old_ses}'):
                shutil.move(dirpath, dirpath.replace(f"ses-{old_ses}",
                                                      f"ses-{new_ses}"))
                
        self.modify_participants_tsv(old_sub=subject, new_sub=subject, old_ses=old_ses, new_ses=new_ses)
    
    
    def rename_sequence(self, old_seq, new_seq, logger=logging):
        """
        

        Parameters
        ----------
        old_seq : TYPE
            DESCRIPTION.
        new_seq : TYPE
            DESCRIPTION.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """
        for path, dirs, files in os.walk(self.root_dir):
            for file in files:
                if old_seq in file:
                    os.rename(pjoin(path, file), pjoin(path, file.replace(old_seq, new_seq)))


    def copy_dicomfolder_to_sourcedata(self, dicomfolder, pat_id, session, logger=logging):
        """
        

        Parameters
        ----------
        dicomfolder : TYPE
            DESCRIPTION.
        pat_id : TYPE
            DESCRIPTION.
        session : TYPE
            DESCRIPTION.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """
        sourcedata = pjoin(self.root_dir, "sourcedata")
        if pexists(pjoin(sourcedata, f"sub-{pat_id}",
                                       f"ses-{session}")) and \
            len(os.listdir(pjoin(sourcedata, f"sub-{pat_id}",
                                       f"ses-{session}"))) > 0:

            logging.error("[ERROR] Error while trying to copy the dicom folder into")
            logging.info(f"sourcedata folder: sourcedata/sub-{pat_id}/ses-{session}")
            logging.info("already exists and is not empty.")
            logging.info(" Please remove this directory and try again.")
            return


        self.mkdir_if_not_exists(sourcedata)
        self.mkdir_if_not_exists(pjoin(sourcedata, f"sub-{pat_id}"))
        self.mkdir_if_not_exists(pjoin(sourcedata, f"sub-{pat_id}",
                                       f"ses-{session}"))

        logging.info("[INFO] Copying dicom folder to sourcedata ...")
        shutil.copytree(dicomfolder, pjoin(sourcedata, f"sub-{pat_id}",
                                       f"ses-{session}", "DICOM"))


    def convert_dicoms_to_bids(self, dicomfolder, pat_id=None, session=None,
                               return_dicom_series=False, logger=logging):
        """
        

        Parameters
        ----------
        dicomfolder : TYPE
            DESCRIPTION.
        pat_id : TYPE, optional
            DESCRIPTION. The default is None.
        session : TYPE, optional
            DESCRIPTION. The default is None.
        return_dicom_series : TYPE, optional
            DESCRIPTION. The default is False.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        
        # print("WTF-bruh ?")

        pat_id = None if pat_id is None else str(int(pat_id)).zfill(3)
        session = None if session is None else str(int(session)).zfill(2)

        # Convert all DICOMs
        dicom_series = self.convert_all_dicoms(dicomfolder, logger=logger)

        # Create directories in the BIDS file structure by giving an incremental id
        # pat_id, session = make_directories(bids_dir,pat_id=None,session=None)
        # To specify the patient id:
        # logging.debug('make directories ?')
        pat_id, session = self.make_directories(pat_id=pat_id,session=session, logger=logger)
        # logging.debug('make directories !')
        # To specify the patient id and session:
        # pat_id, session = make_directories(bids_dir,pat_id='ID_TO_SPECIFY',session='SESSION_TO_SPECIFY')
        # print("Debug, why does it stop")
        # Rename and move all (interesting) converted files into the bids directory
        self.rename_and_move_nifti(dicom_series, pat_id, session, logger=logger)

        self.copy_dicomfolder_to_sourcedata(dicomfolder, pat_id, session, logger=logger)

        # pat_name, pat_date = self.separate_dicoms(dicomfolder, pat_id, session)

        self.anonymisation(pat_id, session, logger=logger)
        
        logging.info(f"[INFO] done for patient {pat_id}")

        if return_dicom_series:
            return pat_id, session, dicom_series
        return pat_id, session


    def separate_dicoms(self, sub, ses, logger=logging):
        """
        

        Parameters
        ----------
        sub : TYPE
            DESCRIPTION.
        ses : TYPE
            DESCRIPTION.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        
        src = pjoin(self.root_dir, f'sourcedata', f'sub-{sub}', f'ses-{ses}')
        
        logging.info('[INFO] Sorting dicoms ...')
        def clean_text(string):
            # clean and standardize text descriptions, which makes searching files easier
            forbidden_symbols = ["*", ".", ",", "\"", "\\", "/", "|", "[", "]", ":", ";", " "]
            for symbol in forbidden_symbols:
                string = string.replace(symbol, "_") # replace everything with an underscore
            return string.lower()

        dst = f"{self.root_dir}/sourcedata/sub-{sub}/ses-{ses}/DICOM/sorted"

        logging.info('reading file list...')
        unsortedList = []
        corresponding_root = []
        for root, dirs, files in os.walk(src):
            for file in files:
                if "." not in file[0] or not any([ext in file for ext in self.wrong_extensions]):# exclude non-dicoms, good for messy folders
                    unsortedList.append(os.path.join(root, file))
                    corresponding_root.append(root)

        logging.info('%s files found.' % len(unsortedList))

        pat_name = None
        pat_date = None

        for dicom_loc in unsortedList:
            # read the file
            ds = dcmread(dicom_loc, force=True)

            if pat_name == None:
                pat_name = ds.get('PatientName')
            if pat_name == None:
                pat_name = ds.get('Name')
            if pat_date == None:
                pat_date = ds.get('ContentDate')
            if pat_date == None:
                pat_date = ds.get('Date')
            if pat_date == None:
                pat_date = ds.get('AcquisitionDate')

            # find folder_name
            path = dicom_loc.split('/')
            folder = path[len(path)-2]

            # get patient, study, and series information
            patientID = clean_text(ds.get("PatientID", "NA"))

            # generate new, standardized file name
            instanceNumber = str(ds.get("InstanceNumber","0"))

            # get scanning sequence
            scanning_sequence = ds.get("SeriesDescription")

            if scanning_sequence == None:
                scanning_sequence = ds.get("SequenceName")

            if scanning_sequence == None:
                scanning_sequence = "NoScanningSequence"
                
            series_number = ds.get("SeriesNumber")
            
            scanning_sequence = clean_text(scanning_sequence)

            fileName = f"{patientID}_{scanning_sequence}_{series_number}_{instanceNumber}.dcm"

            scanning_sequence = f'{folder}_{scanning_sequence}_{series_number}'

            # save files to a 4-tier nested folder structure
            if not os.path.exists(os.path.join(dst, scanning_sequence)):
                os.makedirs(os.path.join(dst, scanning_sequence))

            ds.save_as(os.path.join(dst, scanning_sequence, fileName))

        logging.info('done.')

        return pat_name, pat_date
    
    
    
    def update_dataset_description(self, dataset_description={}):
        with open(pjoin(self.root_dir, 'dataset_description.json'), 'w') as fp:
            json.dump(dataset_description, fp)
    
    

    def update_participants_json(self, new_item):
        if pexists(pjoin(self.root_dir, "participants.json")):
            with open(pjoin(self.root_dir, "participants.json")) as part_json:
                participants_json = json.load(part_json)
        else:
            participants_json = {
                                 "participant_id":{"Description":"Corresponding ID of the participant in the BIDS directory"},
                                 "age":{"Description": "age of the participant",
                                        "Units": "years",
                                        "dicom_tags":["PatientAge"]
                                        },
                                 "sex":{"Description": "sex of the participant as reported by the participant",
                                        "Levels": {"M": "male",
                                                   "F": "female"
                                                   },
                                        "dicom_tags":["PatientSex"]
                                        }
                                 }
        if new_item.get('name') != None or new_item.get('name') != '' and new_item.get('infos') != None:
            participants_json[new_item.get('name')] = new_item.get('infos')
        
        with open(pjoin(self.root_dir, 'participants.json'), 'w') as fp:
            json.dump(participants_json, fp)
        
        self.update_participants_tsv()
        
    
    def update_participants_tsv(self):
        # print('debug')
        
        subjects_and_sessions = []
        for d in os.listdir(pjoin(self.root_dir)):
            if 'sub' in d:
                sub = d.split('-')[1]
                sess = []
                for sub_d in os.listdir(pjoin(self.root_dir, f'sub-{sub}')):
                    if 'ses' in sub_d:
                        ses = sub_d.split('-')[1]
                        sess.append(ses)
                subjects_and_sessions.append((sub, sess))
                    
        # print(subjects_and_sessions)
        for sub, sess in subjects_and_sessions:
            for ses in sess:
                print(sub, ses)
                self.anonymisation(sub, ses)
                    
        
        # wrong_extensions = ['.jsn', '.bval', '.bvec', '.nii', '.gz', '.jpg']
        
        # if pexists(pjoin(self.root_dir, "participants.json")):
        #     with open(pjoin(self.root_dir, "participants.json")) as part_json:
        #         participants_json = json.load(part_json)
        # else:
        #     participants_json = {
        #                          "participant_id":{"Description":"Corresponding ID of the participant in the BIDS directory"},
        #                          "age":{"Description": "age of the participant",
        #                                 "Units": "years",
        #                                 "dicom_tags":["PatientAge"]
        #                                 },
        #                          "sex":{"Description": "sex of the participant as reported by the participant",
        #                                 "Levels": {"M": "male",
        #                                            "F": "female"
        #                                            },
        #                                 "dicom_tags":["PatientSex"]
        #                                 }
        #                          }
            
        # if pexists(pjoin(self.root_dir, "participants.tsv")):
        #     participants_tsv = pd.read_csv(pjoin(self.root_dir, "participants.tsv"), sep='\t').to_dict()
        # else:
        #     participants_tsv = {'participant_id':{}, 'age':{}, 'sex':{}, 'ses-01':{}}
            
        # subs = []
        # for _,dirs,_ in os.walk(pjoin(self.root_dir)):
        #     for d in dirs:
        #         if 'sub' in d:
        #             sub = d
        #             subs.append(sub)
                    
        # for sub in subs:
        #     last_ses = ''
        #     ses = 0
        #     for _,dirs,_ in os.walk(pjoin(self.root_dir, sub)):
        #         for d in dirs:
        #             if 'ses' in d:
        #                 check_ses = int(d.split('-')[1])
        #                 if check_ses > ses:
        #                     ses = check_ses
        #     last_ses = f'ses-{str(ses).zfill(2)}'
            
        #     src = pjoin(self.root_dir, f'sourcedata', sub, last_ses)
        #     participants_json_keys = list(participants_json.keys())
        #     participants_json_keys.remove('participant_id')
        #     tags = [(x, participants_json.get(x).get('dicom_tags')) for x in participants_json_keys]
        #     results = [None]*len(tags)
        #     tags_bool = [False]*len(tags)
        #     for root, dirs, files in os.walk(src):
        #         for file in files:
        #             if "." not in file[0] or not any([ext in file for ext in wrong_extensions]):# exclude non-dicoms, good for messy folders
        #                 # read the file
        #                 ds = dcmread(pjoin(root,file), force=True)
                        
        #                 i = 0
        #                 for tag in tags:
        #                     dcm_tags = tag[1]
        #                     for dcm_tag in dcm_tags:
        #                         val = ds.get(dcm_tag)
        #                         if val != None:
        #                             results[i] = val
        #                             tags_bool[i] = True
        #                             break
        #                     i = i+1
        #             if all(tags_bool):
        #                 break
        #         if all(tags_bool):
        #             break
            
        #     if sub in participants_tsv['participant_id'].keys():
        #         key_num = list(participants_tsv['participant_id'].values()).index(sub)
        #     else:
        #         key_num = len(participants_tsv['participant_id'])
        #     i = 0
        #     for tag in tags:
        #         if tag[0] not in participants_tsv.keys():
        #             participants_tsv[tag[0]] = {}
        #         # update dicionary with the date of the new session
        #         if results[i] != None and results[i] != '':
        #             participants_tsv[tag[0]][key_num] = results[i]
        #         else:
        #             participants_tsv[tag[0]][key_num] = 'n/a'
        #         i = i+1
                
        # # Save anonym dic to csv
        # participants_tsv_df = pd.DataFrame(participants_tsv)
        # participants_tsv_df.to_csv(pjoin(self.root_dir, "participants.tsv"), index=False, sep='\t')


    def anonymisation(self, pat_id, pat_ses, logger=logging):
        """
        

        Parameters
        ----------
        pat_id : TYPE
            DESCRIPTION.
        pat_ses : TYPE
            DESCRIPTION.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """
        
        src = pjoin(self.root_dir, f'sourcedata', f'sub-{pat_id}', f'ses-{pat_ses}')
        
        wrong_extensions = ['.jsn', '.bval', '.bvec', '.nii', '.gz', '.jpg']
        
        # pat_name = None
        # pat_date = None
        # pat_folder_id = None
        save_participants_json = False
        if pexists(pjoin(self.root_dir, "participants.json")):
            with open(pjoin(self.root_dir, "participants.json")) as part_json:
                participants_json = json.load(part_json)
        else:
            participants_json = {
                                 "participant_id":{"Description":"Corresponding ID of the participant in the BIDS directory"},
                                 "age":{"Description": "age of the participant",
                                        "Units": "years",
                                        "dicom_tags":["PatientAge"]
                                        },
                                 "sex":{"Description": "sex of the participant as reported by the participant",
                                        "Levels": {"M": "male",
                                                   "F": "female"
                                                   },
                                        "dicom_tags":["PatientSex"]
                                        },
                                 "ses-01":{"Description":"Date of the MRI session number 01",
                                           "dicom_tags":["AcquisitionDate", "Date"]}
                                 }
            save_participants_json = True
            
        if pexists(pjoin(self.root_dir, "participants.tsv")):
            participants_tsv = pd.read_csv(pjoin(self.root_dir, "participants.tsv"), sep='\t').to_dict()
        else:
            participants_tsv = {'participant_id':{}, 'age':{}, 'sex':{}, 'ses-01':{}}
                        
        if f'ses-{pat_ses}' not in participants_tsv.keys():
            sessions = [x for x in participants_json.keys() if 'ses' in x]
            last_ses = sessions[-1]
            # participants_json[f'ses-{pat_ses}'] = {"Description":"Date of the MRI session number 01", "dicom_tags":["AcquisitionDate", "Date"]}
            participants_json_list = list(participants_json.items())
            participants_tsv_list = list(participants_tsv.items())
            last_ses_idx = list(participants_json.keys()).index(last_ses)
            participants_json_list.insert(last_ses_idx+1, (f'ses-{pat_ses}', {"Description":f"Date of the MRI session number {pat_ses}", "dicom_tags":["AcquisitionDate", "Date"]}))
            participants_tsv_list.insert(last_ses_idx+1, (f'ses-{pat_ses}', {}))
            participants_json = dict(participants_json_list)
            participants_tsv = dict(participants_tsv_list)
            save_participants_json = True
        
        participants_json_keys = list(participants_json.keys())
        participants_json_keys.remove('participant_id')
        sessions = [x for x in participants_json_keys if 'ses' in x]
        for ses in sessions:
            if ses != f'ses-{pat_ses}':
                participants_json_keys.remove(ses)
        # print(participants_json_keys)
        tags = [(x, participants_json.get(x).get('dicom_tags')) for x in participants_json_keys]
        results = [None]*len(tags)
        tags_bool = [False]*len(tags)
        
        for root, dirs, files in os.walk(src):
            for file in files:
                if "." not in file[0] or not any([ext in file for ext in wrong_extensions]):# exclude non-dicoms, good for messy folders
                    # read the file
                    ds = dcmread(pjoin(root,file), force=True)

            #         if pat_name == None:
            #             pat_name = ds.get('PatientName')
            #         if pat_name == None:
            #             pat_name = ds.get('Name')
                    # if pat_date == None:
                    #     pat_date = ds.get('AcquisitionDateTime')
                    # if pat_date == None:
                    #     pat_date = ds.get('AcquisitionDate')
                    # if pat_date == None:
                    #     pat_date = ds.get('Date')
                    # if pat_date == None:
                    #     pat_date = ds.get('ContentDate')
                    # pat_folder_id = ds.get('PatientID')
                
            #     if pat_name != None and pat_date != None and pat_folder_id != None:
            #         break
            
            # if pat_name != None and pat_date != None and pat_folder_id != None:
            #     break
                    i = 0
                    for tag in tags:
                        dcm_tags = tag[1]
                        for dcm_tag in dcm_tags:
                            val = ds.get(dcm_tag)
                            if val != None:
                                results[i] = val
                                tags_bool[i] = True
                                break
                        i = i+1
                if all(tags_bool):
                    break
            if all(tags_bool):
                break

        # # check if new patient
        # if f'sub-{pat_id}' in participants_tsv['participant_id'].keys():
        #     key_num = list(participants_tsv['participant_id'].values()).index(f'sub-{pat_id}')
        #     if f'ses-{pat_ses}' not in anonym.keys():
        #         anonym[f'ses-{pat_ses}'] = {}
        #     # update dicionary with the date of the new session
        #     anonym[f'ses-{pat_ses}'][key_num] = pd.Timestamp(pat_date)
        # else:
        #     # add new patient
        #     key_num = len(anonym['participant_id'])
        #     anonym['participant_name'][key_num] = pat_name
        #     anonym['participant_id'][key_num] = f'sub-{pat_id}'
        #     anonym['patient_id'][key_num] = pat_folder_id
        #     if f'ses-{pat_ses}' not in anonym.keys():   
        #         anonym[f'ses-{pat_ses}'] = {}
        #     anonym[f'ses-{pat_ses}'][key_num] = pd.Timestamp(pat_date)
        
        # if f'sub-{pat_id}' in participants_tsv['participant_id'].keys():
        #     key_num = list(participants_tsv['participant_id'].values()).index(f'sub-{pat_id}')
        #     if f'ses-{pat_ses}' not in participants_tsv.keys():
        #         participants_tsv[f'ses-{pat_ses}'] = {}
        #     # update dicionary with the date of the new session
        #     participants_tsv[f'ses-{pat_ses}'][key_num] = pd.Timestamp(pat_date)
        # else:
        #     # add new patient
        #     key_num = len(participants_tsv['participant_id'])
        #     participants_tsv['participant_id'][key_num] = f'sub-{pat_id}'
        #     if f'ses-{pat_ses}' not in participants_tsv.keys():   
        #         participants_tsv[f'ses-{pat_ses}'] = {}
        #     participants_tsv[f'ses-{pat_ses}'][key_num] = pd.Timestamp(pat_date)
        # print(tags)
        # print(results)
        if f'sub-{pat_id}' in participants_tsv['participant_id'].values():
            key_num = list(participants_tsv['participant_id'].values()).index(f'sub-{pat_id}')
        else:
            # add new patient
            key_num = len(participants_tsv['participant_id'])
            participants_tsv['participant_id'][key_num] = f'sub-{pat_id}'
        i = 0
        for tag in tags:
            if tag[0] not in participants_tsv.keys():
                participants_tsv[tag[0]] = {}
            # update dicionary with the date of the new session
            if 'ses' in tag[0]:
                if results[i] != None and results[i] != '':
                    participants_tsv[tag[0]][key_num] = pd.Timestamp(results[i])
                else:
                    participants_tsv[tag[0]][key_num] = 'n/a'
            else:
                if results[i] != None and results[i] != '':
                    participants_tsv[tag[0]][key_num] = results[i]
                else:
                    participants_tsv[tag[0]][key_num] = 'n/a'
            i = i+1

        # Save anonym dic to csv
        participants_tsv_df = pd.DataFrame(participants_tsv)
        participants_tsv_df.to_csv(pjoin(self.root_dir, "participants.tsv"), index=False, sep='\t')
        
        # Save participants_json
        if save_participants_json:
            with open(pjoin(self.root_dir, 'participants.json'), 'w') as fp:
                json.dump(participants_json, fp)

        logging.info('[INFO] Anonymisation done')
        
        
    def modify_participants_tsv(self, old_sub='', new_sub='', old_ses='', new_ses='', logger=logging):
        """
        

        Parameters
        ----------
        old_sub : TYPE, optional
            DESCRIPTION. The default is ''.
        new_sub : TYPE, optional
            DESCRIPTION. The default is ''.
        old_ses : TYPE, optional
            DESCRIPTION. The default is ''.
        new_ses : TYPE, optional
            DESCRIPTION. The default is ''.
        logger : TYPE, optional
            DESCRIPTION. The default is logging.

        Returns
        -------
        None.

        """
        try:
            participants = pd.read_csv(pjoin(self.root_dir, "participants.tsv"), sep='\t').to_dict()
        except FileNotFoundError: 
            logging.error('participants.tsv does not exists')
            return
        if old_sub == '':
            return 
        try:
            key_num = list(participants['participant_id'].values()).index(f'sub-{old_sub}')
        except ValueError:
            logging.error('sub-{old_sub} is not present in the database (participants.tsv)')
            return
        
        if new_sub == '':
            for key in participants.keys():
                del participants[key][key_num]
        elif new_sub != old_sub:
            participants['participant_id'][key_num] = f'sub-{new_sub}'
        elif new_sub == old_sub:
            if old_ses == '':
                return
            else:
                if f'ses-{old_ses}' not in participants.keys():
                    logging.error(f'Subject {old_sub} does not have a session {old_ses}')
                    pass
                else:
                    if new_ses == '':
                        del participants[f'ses-{old_ses}'][key_num]
                    else:
                        ses_date = participants[f'ses-{old_ses}'][key_num]
                        del participants[f'ses-{old_ses}'][key_num]
                        participants[f'ses-{new_ses}'][key_num] = ses_date
        else:
            pass                    
        participants_df = pd.DataFrame(participants)
        participants_df.to_csv(pjoin(self.root_dir, "participants.tsv"), index=False, sep='\t')


if __name__ == '__main__':
    pass


