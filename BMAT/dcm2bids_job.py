#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 11:45:28 2024

@author: colin
"""

from dicom2bids_cluster import *
import os
from os.path import join as pjoin
from os.path import exists as pexists
import sys
import subprocess
import fcntl
import random
import shutil
import zipfile
import time


def create_iso(folder_path, iso_path):
    # Run genisoimage to create the ISO file
    subprocess.Popen(f"genisoimage -o  {iso_path} -J -r -V ISO_VOLUME_LABEL {folder_path}", shell=True).wait()


def separate_dicoms(input_dir, output_dir):
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
    print('Separate DICOM')
    
    src = input_dir
    
    def clean_text(string):
        # clean and standardize text descriptions, which makes searching files easier
        forbidden_symbols = ["*", ".", ",", "\"", "\\", "/", "|", "[", "]", ":", ";", " "]
        for symbol in forbidden_symbols:
            string = string.replace(symbol, "_") # replace everything with an underscore
        return string.lower()

    dst = output_dir

    print('reading file list...')
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

        fileName = f"{scanning_sequence}_{series_number}_{instanceNumber}.dcm"

        scanning_sequence = f'{folder}_{scanning_sequence}_{series_number}'

        # save files to a 4-tier nested folder structure
        if not os.path.exists(os.path.join(dst, scanning_sequence)):
            os.makedirs(os.path.join(dst, scanning_sequence))

        ds.save_as(os.path.join(dst, scanning_sequence, fileName))

    print('done.')



def zip_folder(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
                


def dcm2bids(bids_path, sub, ses, dicom, unzip=False, seq_f='/storage/platform/ions/nima/BMAT/sequences.csv', iso=False):
    
    # Check the files
    if not pexists(bids_path):
        print('[ERROR] BIDS path does not exist ')
        raise FileNotFoundError('[ERROR] BIDS path does not exist ')
    
    if not pexists(dicom):
        print('[ERROR] dicom path does not exist')
        raise FileNotFoundError('[ERROR] dicom path does not exist')
        
    if not pexists(seq_f):
        print('[ERROR] sequences.csv file for sequences renaming does not exist')
        raise FileNotFoundError('[ERROR] sequences.csv file for sequences renaming does not exist')
        
    if unzip:
        if dicom[-4:] != '.zip':
            print('[ERROR] dicom path does not seem to be a .zip file but the unzip option is selected')
            raise ValueError('[ERROR] dicom path does not seem to be a .zip file but the unzip option is selected')
            
    if pexists(pjoin(bids_path, f'sub-{sub}', f'ses-{ses}')):
        print(f'[ERROR] sub-{sub} and ses-{ses} ID already used')
        raise ValueError(f'[ERROR] sub-{sub} and ses-{ses} ID already used')
            
    sourcedata = pjoin(bids_path, 'sourcedata')
    if not pexists(sourcedata):
        print('[WARNING] source data does not exist, so creating it ...')
        os.makedirs(sourcedata)
    
    if pexists(pjoin(sourcedata, sub, ses)):
        print(f'[ERROR] sub-{sub} and ses-{ses} ID for sourcedata already used')
        raise ValueError(f'[ERROR] sub-{sub} and ses-{ses} ID for sourcedata already used')
    
    # Copy the dicom.zip file into a /tmp directory
    # create a working directory on in the /tmp folder 
    job_id = os.getenv("SLURM_JOB_ID")
    if job_id == None:
        print('[WARNING] could not get the Slurm Job ID')
        job_id = random.randint(0, 999999)
    
    bids_name = bids_path.split(os.sep)[-1]
    
    convert_f = pjoin('/tmp', f'BMAT_{bids_name}_dcm2bids_{job_id}')
    if pexists(convert_f):
        print('[ERROR] convert foler already exists')
        raise FileExistsError('[ERROR] convert foler already exists')
    else:
        os.makedirs(convert_f)
        
    # copy dicom file to conversion folder
    print('copy file to conversion folder')
    dicom_f = dicom.split(os.sep)[-1]
    shutil.copy(dicom, pjoin(convert_f, dicom_f))
    dicom_zip = pjoin(convert_f, dicom_f)
    print(f'{dicom_zip=}')
    
    # unzip the .zip file
    if unzip:
        print('unzip ...')
        directory_to_extract_to = pjoin(convert_f, dicom_f[:-4])
        print(f'{directory_to_extract_to=}')
        with zipfile.ZipFile(dicom_zip, 'r') as zip_ref:
            zip_ref.extractall(directory_to_extract_to)
        dicom_dir = directory_to_extract_to
        dicom_zip = dicom_zip
        print(f'{dicom_dir=}')
        print(f'{dicom_zip=}')
    else:
        print('already unzip')
        dicom_dir = dicom
        dicom_zip = f'{dicom}.zip'
        zip_folder(dicom_dir, dicom_zip)
    
    # # convert dicom to bids
    bids = BIDSHandler(bids_path, sequences_csv=seq_f)
    bids.convert_dicoms_to_bids(dicomfolder=dicom_dir, pat_id=sub, session=ses, return_dicom_series=True, copy_dicomfolder=False)
    
    # copy the dicom.zip into the bids database
    # create sub ses folder in sourcedata
    if not pexists(pjoin(sourcedata, f'sub-{sub}', f'ses-{ses}')):
        os.makedirs(pjoin(sourcedata, f'sub-{sub}', f'ses-{ses}'))
    shutil.copy(dicom_zip, pjoin(sourcedata, f'sub-{sub}', f'ses-{ses}', 'DICOM.zip'))
    
    # time.sleep(1000)
    
    # if iso
    if iso:
        print('make iso ...')
        
        # separate dicom into sequences folder
        print('separate dicom into sequences folder ...')
        output_dir = pjoin(convert_f, 'DICOM_separated')
        print(f'{output_dir=}')
        separate_dicoms(dicom_dir, output_dir)
    
        # convert each sequences folder in an iso
        for seq in os.listdir(output_dir):
            seq_iso = f'{seq}.iso'
            create_iso(pjoin(output_dir, seq), pjoin(output_dir, seq_iso))
        
        # copy the iso sequences in the bids database
        sourcedata_iso = pjoin(sourcedata, f'sub-{sub}', f'ses-{ses}', 'DICOM_iso')
        if not pexists(sourcedata_iso):
            os.makedirs(sourcedata_iso)
        print(f'{sourcedata_iso=}')
        for seq in os.listdir(output_dir):
            if not os.path.isdir(seq):
                if seq[-4:] == '.iso':
                    shutil.copy(pjoin(output_dir, seq), pjoin(sourcedata_iso, seq))
                    
    # remove temp folder
    shutil.rmtree(convert_f)



if __name__ == '__main__':
    
    help_message = '''
dcm2bids_job        
    Automatic script to convert DICOM into a bids databse via a slurm job
    
use:
    python dcm2bids.py bids_path sub ses dicom_folder [options]
    
Compulsory arguments:
    
    bids_path: path towards the BIDS root directory
    
    sub: subject id (or ids separated by comma) in the BIDS database (all by default)
    
    ses: session id (or ids separated by comma) in the BIDS database (all by default)
    
    dicom_folder: folder that contains the dicom to convert to the bids_database
            
Optional arguments:     

    -z or --unzip:
        used if the dicom_folder is in a .zip format to unzip it before doing the convertion
        
    -seq or --sequences seq:
        seq: path towards the seqences.csv file to use for renaming of the sequences
            default: nima/BMAT/sequences.csv
    
    -iso or --iso-format:
        put in the database the sequences in an .iso format 
        default: False
        
    -h or --help:
            display help message
    
    '''
    
    if len(sys.argv) < 4:
        print('Not enough arguments')
        print(help_message)
        sys.exit(0)
        
    bids_path = sys.argv[1]   
    sub = sys.argv[2]
    ses = sys.argv[3]
    dicom = sys.argv[4]
    unzip = False
    seq_f = '/storage/platform/ions/nima/BMAT/sequences.csv'
    iso = False
        
    i = 5
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '-z' or arg == '--unzip':
            unzip = True
            i = i+1
        elif arg == '-seq' or arg == '--sequences':
            seq_f = sys.argv[i+1]
            i = i+2
        elif arg == '-iso' or arg == '--iso-format':
            iso = True
            i = i+1
        elif arg == '-h' or arg == '--help':
            print(help_message)
            sys.exit(0)
        else:
            print(f'Unrecognized argument: {arg}\n')
            print(help_message)
            sys.exit(0)
    
    subjects_and_sessions = []
    
    if sub == 'all':
        for dirs in os.listdir(bids_path):
            if 'sub-' in dirs:
                subj = dirs.split('-')[1]
                sess = []
                if ses == 'all':
                    for d in os.listdir(pjoin(bids_path, f'sub-{subj}')):
                        if 'ses-' in d:
                            s = d.split('-')[1]
                            sess.append(s)
                else:
                    ses_details = ses.split(',')
                    for s in ses_details:
                        if os.path.isdir(pjoin(bids_path, f'sub-{subj}', f'ses-{s}')):
                            sess.append(s)
                subjects_and_sessions.append((subj, sess))
        
    else:
    
        sub_details = sub.split(',')
        ses_details = ses.split(',')
        
        for sub in sub_details:
            sess = []
            for ses in ses_details:
                sess.append(ses)
            subjects_and_sessions.append((sub, sess))
            
    for sub, sess in subjects_and_sessions:
        for ses in sess:
            print(sub, ses)
            
            dcm2bids(bids_path, sub, ses, dicom, unzip=unzip, seq_f=seq_f, iso=iso)            