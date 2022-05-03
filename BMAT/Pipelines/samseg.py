#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 10 14:25:40 2021

@author: ColinVDB
rec-star_FLAIR
"""


import sys
import os
from os.path import join as pjoin
from os.path import exists as pexists
# from dicom2bids import *
import logging
from PyQt5.QtCore import (QSize,
                          Qt,
                          QModelIndex,
                          QMutex,
                          QObject,
                          QThread,
                          pyqtSignal,
                          QRunnable,
                          QThreadPool)
from PyQt5.QtWidgets import (QDesktopWidget,
                             QApplication,
                             QWidget,
                             QPushButton,
                             QMainWindow,
                             QLabel,
                             QLineEdit,
                             QVBoxLayout,
                             QHBoxLayout,
                             QFileDialog,
                             QDialog,
                             QTreeView,
                             QFileSystemModel,
                             QGridLayout,
                             QPlainTextEdit,
                             QMessageBox,
                             QListWidget,
                             QTableWidget,
                             QTableWidgetItem,
                             QMenu,
                             QAction,
                             QTabWidget,
                             QCheckBox)
from PyQt5.QtGui import (QFont,
                         QIcon)
import traceback
import threading
import subprocess
import pandas as pd
import platform
import json
from bids_validator import BIDSValidator
import time
import shutil
import docker
import nibabel as nib


# from my_logging import setup_logging
from tqdm.auto import tqdm


def launch(parent):
    """
    

    Parameters
    ----------
    parent : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    window = MainWindow(parent)
    window.show()
    
    

# =============================================================================
# MainWindow
# =============================================================================
class MainWindow(QMainWindow):
    """
    """
    

    def __init__(self, parent):
        """
        

        Parameters
        ----------
        parent : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        super().__init__()
        self.parent = parent
        self.bids = self.parent.bids

        self.setWindowTitle("Rec-star_FLAIR computation")
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.center()
        
        self.tab = SamsegTab(self)
        layout = QVBoxLayout()
        layout.addWidget(self.tab)

        self.window.setLayout(layout)


    def center(self):
        """
        

        Returns
        -------
        None.

        """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())



# =============================================================================
# FlairStarTab
# =============================================================================
class SamsegTab(QWidget):
    """
    """
    

    def __init__(self, parent):
        """
        

        Parameters
        ----------
        parent : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        super().__init__()
        self.parent = parent
        self.bids = self.parent.bids
        self.setMinimumSize(500, 200)
        
        self.normalization_check = QCheckBox('Normalization')
        self.normalization_check.stateChanged.connect(self.normalization_clicked)
        self.normalization = False
        
        self.mprage_check = QCheckBox('MPRAGE')
        self.mprage_check.stateChanged.connect(self.mprage_clicked)
        self.mprage = False
        
        self.step1_check = QCheckBox('Preprocessing')
        self.step1_check.stateChanged.connect(self.step1_clicked)
        self.step1 = False
        
        self.step2_check = QCheckBox('Segmentation')
        self.step2_check.stateChanged.connect(self.step2_clicked)
        self.step2 = False
        
        # self.step3_check = QCheckBox('Mask Binarization')
        # self.step3_check.stateChanged.connect(self.step3_clicked)
        # self.step3 = False
        
        self.subjects_input = QLineEdit(self)
        self.subjects_input.setPlaceholderText("Select subjects")

        self.sessions_input = QLineEdit(self)
        self.sessions_input.setPlaceholderText("Select sessions")
        
        self.samseg_button = QPushButton("Run Segmentation")
        self.samseg_button.clicked.connect(self.samseg_computation)
        
        layout = QVBoxLayout()
        layout.addWidget(self.normalization_check)
        layout.addWidget(self.mprage_check)
        layout.addWidget(self.step1_check)
        layout.addWidget(self.step2_check)
        # layout.addWidget(self.step3_check)
        layout.addWidget(self.subjects_input)
        layout.addWidget(self.sessions_input)
        layout.addWidget(self.samseg_button)
        
        self.setLayout(layout)
        
    
    def normalization_clicked(self, state):
        if state == Qt.Checked:
            self.normalization = True
        else:
            self.normalization = False
            
    
    def mprage_clicked(self, state):
        if state == Qt.Checked:
            self.mprage = True
        else:
            self.mprage = False
            
            
    def step1_clicked(self, state):
        if state == Qt.Checked:
            self.step1 = True
        else:
            self.step1 = False
            
            
    def step2_clicked(self, state):
        if state == Qt.Checked:
            self.step2 = True
        else:
            self.step2 = False
            
            
    # def step3_clicked(self, state):
    #     if state == Qt.Checked:
    #         self.step3 = True
    #     else:
    #         self.step3 = False
        

    def samseg_computation(self):
        """
        

        Returns
        -------
        None.

        """
        subjects = self.subjects_input.text()
        sessions = self.sessions_input.text()
        self.subjects = []
        # find subjects
        if subjects == 'all':
            all_directories = [x for x in next(os.walk(self.bids.root_dir))[1]]
            for sub in all_directories:
                if sub.find('sub-') == 0:
                    self.subjects.append(sub.split('-')[1])
        else:
            subjects_split = subjects.split(',')
            for sub in subjects_split:
                if '-' in sub:
                    inf_bound = sub.split('-')[0]
                    sup_bound = sub.split('-')[1]
                    fill = len(inf_bound)
                    inf = int(inf_bound)
                    sup = int(sup_bound)
                    for i in range(inf,sup+1):
                        self.subjects.append(str(i).zfill(fill))
                else:
                    self.subjects.append(sub)

        # find sessions
        self.sessions = []
        if sessions == 'all':
            self.sessions.append('all')
        else:
            sessions_split = sessions.split(',')
            for ses in sessions_split:
                if '-' in ses:
                    inf_bound = ses.split('-')[0]
                    sup_bound = ses.split('-')[1]
                    fill = len(inf_bound)
                    inf = int(inf_bound)
                    sup = int(sup_bound)
                    for i in range(inf, sup+1):
                        self.sessions.append(str(i).zfill(fill))
                else:
                    self.sessions.append(ses)

        self.subjects_and_sessions = []
        for sub in self.subjects:
            if len(self.sessions) != 0:
                if self.sessions[0] == 'all':
                    all_directories = [x for x in next(os.walk(pjoin(self.bids.root_dir,f'sub-{sub}')))[1]]
                    sub_ses = []
                    for ses in all_directories:
                        if ses.find('ses-') == 0:
                            sub_ses.append(ses.split('-')[1])
                    self.subjects_and_sessions.append((sub,sub_ses))
                else:
                    self.subjects_and_sessions.append((sub,self.sessions))
        
        for sub, sess in self.subjects_and_sessions:
            for ses in sess:                 
                self.thread = QThread()
                self.action = LesVoLocSegWorker(self.bids, sub, ses, self.normalization, self.mprage, self.step1, self.step2)
                self.action.moveToThread(self.thread)
                self.thread.started.connect(self.action.run)
                self.action.finished.connect(self.thread.quit)
                self.action.finished.connect(self.action.deleteLater)
                self.thread.finished.connect(self.thread.deleteLater)
                last = (sub == self.subjects_and_sessions[-1][0] and ses == sess[-1])
                self.thread.finished.connect(lambda last=last: self.end_pipeline(last))
                self.thread.start()
        
        self.parent.hide()
        
        
    def end_pipeline(self, last):
        """
        

        Parameters
        ----------
        last : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if last:
            logging.info("SAMSEG Pipeline has finished working")



# =============================================================================
# LesVolocSegWorker
# =============================================================================
class LesVoLocSegWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, bids, sub, ses, normalization, mprage, step1, step2):
        """
        
        
        Parameters
        ----------
        bids : TYPE
          DESCRIPTION.
        sub : TYPE
          DESCRIPTION.
        ses : TYPE
          DESCRIPTION.
        normalization : TYPE #True to decrease images resolution
          DESCRIPTION.
        mprage : TYPE        #True if mprage available
          DESCRIPTION.
        step1 : TYPE         #True to execute the preprocessing part
          DESCRIPTION.
        step2 : TYPE         #True to execute SAMSEG segmentation: Produce lesion probability mask
          DESCRIPTION.
        step3 : TYPE         #True to binarize the lesion probability mask
          DESCRIPTION.
        
        Returns
        -------
        None.
        
        """
        super().__init__()
        self.bids = bids
        self.sub = sub
        self.ses = ses
        self.normalization = normalization 
        self.mprage = mprage               
        self.step1 = step1                 
        self.step2 = step2 
        # self.step3 = step3      
        print(f'{normalization=}')
        print(f'{mprage=}')
        print(f'{step1=}')
        print(f'{step2=}')
        self.client = docker.from_env()
      
  
    def run(self): 
        
        # Define the directories for a certain SUBJECT and SESSION
        
        derivative = 'SAMSEG'
        segment = 'segmentation'
        transfo = 'transformation'
        sub_ses_directory = pjoin(self.bids.root_dir, f'sub-{self.sub}', f'ses-{self.ses}', 'anat')
        flair = f'sub-{self.sub}_ses-{self.ses}_FLAIR.nii.gz'
        mprage = f'sub-{self.sub}_ses-{self.ses}_acq-MPRAGE_T1w.nii.gz'
        license_location = f'/home/stluc/Programmes/freesurfer'
        #create directories
        directorysegment = [pjoin('derivatives', derivative), pjoin('derivatives', derivative, segment), pjoin('derivatives', derivative, segment, f'sub-{self.sub}'), pjoin('derivatives', derivative, segment, f'sub-{self.sub}', f'ses-{self.ses}')]
        directorytransfo = [pjoin('derivatives', derivative), pjoin('derivatives', derivative, transfo),pjoin('derivatives', derivative, transfo, f'sub-{self.sub}'), pjoin('derivatives', derivative, transfo, f'sub-{self.sub}', f'ses-{self.ses}')]
        
        self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = directorysegment)
        self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = directorytransfo)
        sub_ses_derivative_path_segment = pjoin(self.bids.root_dir, 'derivatives', derivative, segment, f'sub-{self.sub}', f'ses-{self.ses}')
        sub_ses_derivative_path_transfo = pjoin(self.bids.root_dir, 'derivatives', derivative, transfo, f'sub-{self.sub}', f'ses-{self.ses}')
          
          
        #Perform Segmentation with SAMSEG step by step
        
        #Step1 : Preprocessing (normalization and registration FLAIR and MPRAGE)
        if self.step1 == True: 
            
            print('step1')
          
            if self.normalization == True:
                print('normalization')
              
                # #Pas encore possible de gérer a cause des autorisations
                # #Faut renommer le dossier manuellement et trouver comment le supprimer
                # #Remove existing file that will be recomputed in the directory
                if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_FLAIR_used')):
                    shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_FLAIR_used'))
                if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_MPRAGE_used.nii.gz')):
                    shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_MPRAGE_used.nii.gz'))
                
                
                # # Resize FLAIR to have 256x256x256, 1mm3
                try:
                    logging.info(f'Resizing FLAIR for sub-{self.sub} ses-{self.ses}...')
                    
                    # a la sortie de motioncor --> ce qui nous intéresse c'est le fichier orig.mgz qui est dans
                    # sub_ses_derivative_path_transfo/sub-{self.sub}_FLAIR_used/mri
                    # /usr/local/freesurfer/subjects
                    resize = f'recon-all -motioncor -i /input/{flair} -subjid sub-{self.sub}_FLAIR_used -sd /usr/local/freesurfer/subjects'
                    
                    subprocess.Popen(f'recon-all -motioncor -i {sub_ses_directory}/{flair} -subjid sub-{self.sub}_FLAIR_used -sd {sub_ses_derivative_path_transfo}', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data',f'{sub_ses_directory}:/input', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects' ], command=resize)
                    #subprocess.Popen(f'docker run --rm -e FS_LICENSE=/data/license.txt -v {license_location}:/data -v {sub_ses_directory}:/input -v {sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects freesurfer/freesurfer:7.2.0 {resize}', shell=True).wait()
                    #print(f'docker run --rm -e FS_LICENSE=/data/license.txt -v {license_location}:/data -v {sub_ses_directory}:/input -v {sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects freesurfer/freesurfer:7.2.0 {resize}')
                    
                except Exception as e:
                    print(f'Error {e} when resizing FLAIR for sub-{self.sub}_ses-{self.ses}!')
                
                # Convert mgz file from freesurfer to nii file 
                try:
                    logging.info(f'Converting FLAIR_used.mgz to .nii.gz for sub-{self.sub} ses-{self.ses}...')
                     
                    convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_FLAIR_used/mri/orig.mgz /usr/local/freesurfer/subjects/sub-{self.sub}_FLAIR_used.nii.gz'
                    #3eme path vers l'endroit où se trouve la license
                    
                    subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_FLAIR_used/mri/orig.mgz {sub_ses_derivative_path_transfo}/sub-{self.sub}_FLAIR_used.nii.gz', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True,environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
                 
                except Exception as e:
                    logging.info(f'Error {e} when converting FLAIR_used.mgz to .nii.gz for sub-{self.sub}_ses{self.ses}!')
                     
                # Register MPRAGE on FLAIR 
                if self.mprage == True:
                    print('step1 mprage')
                    try:
                        logging.info(f'Registration of MPRAGE on FLAIR_used for sub-{self.sub} ses-{self.ses}...')
                         
                        register = f'/opt/ants/bin/antsRegistrationSyNQuick.sh -d 3 -n 4 -f /data/sub-{self.sub}_FLAIR_used.nii.gz -m /media/{mprage} -t r -o sub-{self.sub}_MPRAGE_used'
                        
                        subprocess.Popen(f'$ANTs_registration -d 3 -n 4 -f {sub_ses_derivative_path_transfo}/sub-{self.sub}_FLAIR_used.nii.gz -m {sub_ses_directory}/{mprage} -t r -o sub-{self.sub}_MPRAGE_used', shell=True).wait()
                        
                        # self.client.containers.run('antsx/ants', auto_remove=True, volumes=[f'{sub_ses_derivative_path_transfo}:/data', f'{sub_ses_directory}:/media'], command=register)
                     
                        # Change the name of registration output
                        shutil.move(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_MPRAGE_usedWarped.nii.gz'), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_MPRAGE_used.nii.gz'))
                    
                    except Exception as e:
                        logging.error(f'Error {e} during registration of MPRAGE on FLAIR_used for sub-{self.sub}_ses{self.ses}!')
                   
                    #PAs encore utilise    
            else: #pas de resize -> juste registration de MPRAGE sur FLAIR  
            
                print('no normalization')
            
                if self.mprage == True:
                    print('no normalization mprage')
              
                    try:
                        logging.info(f'Registration of MPRAGE on FLAIR_used for sub-{self.sub} ses-{self.ses}...')
                        
                        #Remove existing file that will be recomputed in the directory
                        #os.remove(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_FLAIR_used.nii.gz'))
                        #os.remove(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_MPRAGE_used.nii.gz'))
                        if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_FLAIR_used')):
                            shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_FLAIR_used'))
                        if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_MPRAGE_used.nii.gz')):
                            shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_MPRAGE_used.nii.gz'))
                      
                        #Copy FLAIR in directory of transformations for access simplicity
                        shutil.copyfile(pjoin(sub_ses_directory, flair), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_FLAIR_used.nii.gz'))
                        
                        register = f'/opt/ants/bin/antsRegistrationSyNQuick.sh -d 3 -n 4 -f /data/sub-{self.sub}_FLAIR_used.nii.gz -m /media/{mprage} -t r -o sub-{self.sub}_MPRAGE_used'
                        
                        subprocess.Popen(f'$ANTs_registration -d 3 -n 4 -f {sub_ses_derivative_path_transfo}/sub-{self.sub}_FLAIR_used.nii.gz -m {sub_ses_directory}/{mprage} -t r -o sub-{self.sub}_MPRAGE_used', shell=True).wait()
                        
                        # self.client.containers.run('antsx/ants', auto_remove=True, volumes=[f'{sub_ses_derivative_path_transfo}:/data', f'{sub_ses_directory}:/media'], command=register)
                        
                        # Change the name of registration output
                        shutil.move(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_MPRAGE_usedWarped.nii.gz'), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_MPRAGE_used.nii.gz'))
                    
                    except Exception as e:
                        print(f'Error {e} during registration of MPRAGE on FLAIR_used for sub-{self.sub}_ses{self.ses}!')
                
                
        # Step2 : Segmentation using SAMSEG to compute lesion probability mask
        if self.step2 == True:
            print('step 2')
            
            if self.mprage == True:
                print('step2 mprage')
                try:
                    logging.info(f'Running Samseg for sub-{self.sub} ses-{self.ses}...')
                    
                    #mri_convert pour avoir les FLAIR et MPRAGE_used en mgz au bon endroit
                    convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_FLAIR_used.nii.gz /usr/local/freesurfer/subjects/sub-{self.sub}_FLAIR_used.mgz'
                    
                    subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_FLAIR_used.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_FLAIR_used.mgz', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
                    convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_MPRAGE_used.nii.gz /usr/local/freesurfer/subjects/sub-{self.sub}_MPRAGE_used.mgz'
                    
                    subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_MPRAGE_used.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_MPRAGE_used.mgz', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
                 
                    
                    # https://surfer.nmr.mgh.harvard.edu/fswiki/Samseg
                    samseg = f'run_samseg -i /input/sub-{self.sub}_MPRAGE_used.mgz -i /input/sub-{self.sub}_FLAIR_used.mgz --lesion --lesion-mask-pattern 0 1 --threads 4 -o /media --save-posteriors'
                    
                    subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_MPRAGE_used.mgz -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_FLAIR_used.mgz --lesion --lesion-mask-pattern 0 1 --threads 4 -o {sub_ses_derivative_path_segment} --save-posteriors', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/input', f'{sub_ses_derivative_path_segment}:/media'],command=samseg)
                    #subprocess.Popen(f'docker run --rm -e FS_LICENSE=/data/license.txt -v {license_location}:/data -v {sub_ses_derivative_path_transfo}:/input -v {sub_ses_derivative_path_segment}:/media freesurfer/freesurfer:7.2.0 {samseg}', shell=True).wait()
                    
                    convert = f'mri_convert /usr/local/freesurfer/subjects/posteriors/Lesions.mgz /usr/local/freesurfer/subjects/sub-{self.sub}_lesions.nii.gz'
                    
                    subprocess.Popen(f'mri_convert {sub_ses_derivative_path_segment}/posteriors/Lesions.mgz {sub_ses_derivative_path_segment}/sub-{self.sub}_lesions.nii.gz', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_segment}:/usr/local/freesurfer/subjects'], command=convert)
                  
                  
               
            
                # Change the name of segmentation output
                #shutil.move(pjoin(sub_ses_derivative_path_segment, f'seg.mgz'), pjoin(sub_ses_derivative_path_segment, f'sub{self.sub}_lesions.mgz'))
                except Exception as e:
                    print(f'Error {e} while running Samseg for sub-{self.sub}_ses{self.ses}!')
            else:
                print('step2 no mprage')
                try:
                    logging.info(f'Running Samseg for sub-{self.sub} ses-{self.ses}...')
                    
                    #mri_convert pour avoir les FLAIR et MPRAGE_used en mgz au bon endroit
                    convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_FLAIR_used.nii.gz /usr/local/freesurfer/subjects/sub-{self.sub}_FLAIR_used.mgz'
                    
                    subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_FLAIR_used.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_FLAIR_used.mgz', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
                    # convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_MPRAGE_used.nii.gz /usr/local/freesurfer/subjects/sub-{self.sub}_MPRAGE_used.mgz'
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
                 
                    
                    # https://surfer.nmr.mgh.harvard.edu/fswiki/Samseg
                    samseg = f'run_samseg -i /input/sub-{self.sub}_FLAIR_used.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o /media --save-posteriors'
                    
                    subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_FLAIR_used.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o {sub_ses_derivative_path_segment} --save-posteriors', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/input', f'sub_ses_derivative_path_segment:/media'],command=samseg)
                    #subprocess.Popen(f'docker run --rm -e FS_LICENSE=/data/license.txt -v {license_location}:/data -v {sub_ses_derivative_path_transfo}:/input -v {sub_ses_derivative_path_segment}:/media freesurfer/freesurfer:7.2.0 {samseg}', shell=True).wait()
                    
                    convert = f'mri_convert /usr/local/freesurfer/subjects/posteriors/Lesions.mgz /usr/local/freesurfer/subjects/sub-{self.sub}_lesions.nii.gz'
                    
                    subprocess.Popen(f'mri_convert {sub_ses_derivative_path_segment}/posteriors/Lesions.mgz {sub_ses_derivative_path_segment}/sub-{self.sub}_lesions.nii.gz', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_segment}:/usr/local/freesurfer/subjects'], command=convert)
              
              
           
        
                # Change the name of segmentation output
                #shutil.move(pjoin(sub_ses_derivative_path_segment, f'seg.mgz'), pjoin(sub_ses_derivative_path_segment, f'sub{self.sub}_lesions.mgz'))
                except Exception as e:
                    print(f'Error {e} while running Samseg for sub-{self.sub}_ses{self.ses}!')
             
            #Binarizing the lesion probability  mask     
            try:
                logging.info(f'Binarizing lesion probability mask for sub-{self.sub} ses-{self.ses}...')
               
                threshold = 0.5
                image = nib.load(f'{sub_ses_derivative_path_segment}/posteriors/Lesions.mgz')
                lesions = image.get_fdata()
                lesions[lesions >= threshold] = 1
                lesions[lesions < threshold] = 0
            
                nifti_out = nib.Nifti1Image(lesions, affine=image.affine)
                nib.save(nifti_out, f'{sub_ses_derivative_path_segment}/sub{self.sub}_lesions_binary.nii.gz')
                
            except Exception as e:
                print(f'Error {e} while binarizing lesion probability mask for sub-{self.sub}_ses{self.ses}!')
                
        print('end SAMSEG')
               
        # # Step3 : Binarizing the lesion probability mask
        # if(self.step3 == True):
         
        #     threshold = 0.5
        #     image = nib.load(f'{sub_ses_derivative_path_segment}/posteriors/Lesions.mgz')
        #     lesions = image.get_fdata()
        #     lesions[lesions >= threshold] = 1
        #     lesions[lesions < threshold] = 0
           
        #     nifti_out = nib.Nifti1Image(lesions, affine=image.affine)
        #     nib.save(nifti_out, f'{sub_ses_derivative_path_segment}/sub{self.sub}_lesions_binary.nii.gz')
          
          