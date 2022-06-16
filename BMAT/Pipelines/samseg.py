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
import numpy as np
import numpy.ma as ma
import os
from scipy.ndimage.measurements import label
from scipy.ndimage.morphology import binary_dilation
import faulthandler


# from my_logging import setup_logging
from tqdm.auto import tqdm

# faulthandler.enable()

def launch(parent, add_info=None):
    """
    

    Parameters
    ----------
    parent : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    window = MainWindow(parent, add_info)
    window.show()
    # if not QApplication.instance():
    #     app = QApplication(sys.argv)
    # else:
    #     app = QApplication.instance()

    # # app = QApplication(sys.argv)

    # window = MainWindow(parent)

    # window.show()

    # app.exec()
    
    

# =============================================================================
# MainWindow
# =============================================================================
class MainWindow(QMainWindow):
    """
    """
    

    def __init__(self, parent, add_info):
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
        self.add_info = add_info

        self.setWindowTitle("LesVolLoc")
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.center()
        
        self.tab = SamsegTab(self)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tab)

        self.window.setLayout(self.layout)


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
# SamsegTab
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
        
        self.recon_all_check = QCheckBox('Recon-all')
        self.recon_all_check.stateChanged.connect(self.recon_all_clicked)
        self.recon_all = False
        
        self.step3_check = QCheckBox('Volumetry')
        self.step3_check.stateChanged.connect(self.step3_clicked)
        self.step3 = False
        
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
        layout.addWidget(self.recon_all_check)
        layout.addWidget(self.step3_check)
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
            
    def recon_all_clicked(self, state):
        if state == Qt.Checked:
            self.recon_all = True
        else:
            self.recon_all = False
            
    
    def step3_clicked(self, state):
        if state == Qt.Checked:
            self.step3 = True
        else:
            self.step3 = False
        

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
                         
        self.thread = QThread()
        self.action = LesVolLocSegWorker(self.bids, self.subjects_and_sessions, self.normalization, self.mprage, self.step1, self.step2, self.recon_all, self.step3)
        self.action.moveToThread(self.thread)
        self.thread.started.connect(self.action.run)
        self.action.finished.connect(self.thread.quit)
        self.action.finished.connect(self.action.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        # last = (sub == self.subjects_and_sessions[-1][0] and ses == sess[-1])
        # self.thread.finished.connect(lambda: self.end_pipeline(True))
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
# LesVolLocSegWorker
# =============================================================================
class LesVolLocSegWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, bids, subjects_and_sessions, normalization, mprage, step1, step2, recon_all, step3):
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
        self.subjects_and_sessions = subjects_and_sessions
        self.normalization = normalization 
        self.mprage = mprage               
        self.step1 = step1                 
        self.step2 = step2 
        self.recon_all = recon_all
        self.step3 = step3      
        print(f'{normalization=}')
        print(f'{mprage=}')
        print(f'{step1=}')
        print(f'{step2=}')
        # self.client = docker.from_env()
        
        
    def run(self):
        for sub, sess in self.subjects_and_sessions:
            for ses in sess:
                self.sub = sub
                self.ses = ses
                print(f'Running LesVolLoc for sub-{sub} ses-{ses}')
                self.run_LesVolLoc()
                print(f'LesVolLoc has processed sub-{sub} ses-{ses}')
        self.finished.emit()
    
    def run_LesVolLoc_2(self):
        time.sleep(100)
  
    def run_LesVolLoc(self): 
        
        # Define the directories for a certain SUBJECT and SESSION
        fs = 'FreeSurfer'
        derivative = 'LesVolLoc'
        samseg = 'SAMSEG'
        segment = 'segmentation'
        transfo = 'transformation'
        sub_ses_directory = pjoin(self.bids.root_dir, f'sub-{self.sub}', f'ses-{self.ses}', 'anat')
        flair = f'sub-{self.sub}_ses-{self.ses}_FLAIR.nii.gz'
        mprage = f'sub-{self.sub}_ses-{self.ses}_acq-MPRAGE_T1w.nii.gz'
        # license_location = f'/home/stluc/Programmes/freesurfer'
        #create directories
        directorysegment = [pjoin('derivatives', derivative), pjoin('derivatives', derivative, f'sub-{self.sub}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, segment)]
        directorytransfo = [pjoin('derivatives', derivative), pjoin('derivatives', derivative, f'sub-{self.sub}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, transfo)]
        
        self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = directorysegment)
        self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = directorytransfo)
        sub_ses_derivative_path_segment = pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, segment)
        sub_ses_derivative_path_transfo = pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, transfo)
        sub_ses_derivative_path_stats = pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, 'stats')
        #dossier dans lequel on est sense mettre les resultats de recon-all de fs
        directory_fs_sub_ses = [pjoin('derivatives', derivative), pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}'), pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}'), pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', fs)]
        sub_ses_fs_path = pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', fs)
          
        #Perform Segmentation with SAMSEG step by step
        
        #Step1 : Preprocessing (normalization and registration FLAIR and MPRAGE)
        if self.step1 == True: 
            
            print('step1')
          
            if self.normalization == True:
                print('normalization')
              
                # #Pas encore possible de gérer a cause des autorisations
                # #Faut renommer le dossier manuellement et trouver comment le supprimer
                # #Remove existing file that will be recomputed in the directory
                if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_used')):
                    shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_used'))
                if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz')):
                    shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz'))
                          
                # # Resize FLAIR to have 256x256x256, 1mm3
                try:
                    logging.info(f'Resizing FLAIR for sub-{self.sub} ses-{self.ses}...')
                    
                    # a la sortie de motioncor --> ce qui nous intéresse c'est le fichier orig.mgz qui est dans
                    # sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_used/mri
                    # /usr/local/freesurfer/subjects
                    #resize = f'recon-all -motioncor -i /input/{flair} -subjid sub-{self.sub}_ses-{self.ses}_FLAIR_used -sd /usr/local/freesurfer/subjects'
                    
                    subprocess.Popen(f'recon-all -motioncor -i {sub_ses_directory}/{flair} -subjid sub-{self.sub}_ses-{self.ses}_FLAIR_used -sd {sub_ses_derivative_path_transfo}', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data',f'{sub_ses_directory}:/input', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects' ], command=resize)
                    #subprocess.Popen(f'docker run --rm -e FS_LICENSE=/data/license.txt -v {license_location}:/data -v {sub_ses_directory}:/input -v {sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects freesurfer/freesurfer:7.2.0 {resize}', shell=True).wait()
                    #print(f'docker run --rm -e FS_LICENSE=/data/license.txt -v {license_location}:/data -v {sub_ses_directory}:/input -v {sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects freesurfer/freesurfer:7.2.0 {resize}')
                    
                except Exception as e:
                    print(f'Error {e} when resizing FLAIR for sub-{self.sub}_ses-{self.ses}!')
                
                # Convert mgz file from freesurfer to nii file 
                try:
                    logging.info(f'Converting FLAIR_used.mgz to .nii.gz for sub-{self.sub} ses-{self.ses}...')
                     
                    #convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_FLAIR_used/mri/orig.mgz /usr/local/freesurfer/subjects/sub-{self.sub}_FLAIR_used.nii.gz'
                    #3eme path vers l'endroit où se trouve la license
                    
                    subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used/mri/orig.mgz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True,environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
                 
                except Exception as e:
                    logging.info(f'Error {e} when converting FLAIR_used.mgz to .nii.gz for sub-{self.sub}_ses{self.ses}!')
                     
                # Register MPRAGE on FLAIR 
                if self.mprage == True:
                    print('step1 mprage')
                    try:
                        logging.info(f'Registration of MPRAGE on FLAIR_used for sub-{self.sub} ses-{self.ses}...')
                         
                        #register = f'/opt/ants/bin/antsRegistrationSyNQuick.sh -d 3 -n 4 -f /data/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz -m /media/{mprage} -t r -o sub-{self.sub}_ses-{self.ses}_MPRAGE_used'
                        
                        subprocess.Popen(f'$ANTs_registration -d 3 -n 4 -f {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz -m {sub_ses_directory}/{mprage} -t r -o {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_used', shell=True).wait()
                        
                        # self.client.containers.run('antsx/ants', auto_remove=True, volumes=[f'{sub_ses_derivative_path_transfo}:/data', f'{sub_ses_directory}:/media'], command=register)
                     
                        # Change the name of registration output
                        shutil.move(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_usedWarped.nii.gz'), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz'))
                    
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
                        if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_used')):
                            shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_used'))
                        if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz')):
                            shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz'))
                      
                        #Copy FLAIR in directory of transformations for access simplicity
                        shutil.copyfile(pjoin(sub_ses_directory, flair), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz'))
                        
                        #register = f'/opt/ants/bin/antsRegistrationSyNQuick.sh -d 3 -n 4 -f /data/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz -m /media/{mprage} -t r -o sub-{self.sub}_ses-{self.ses}_MPRAGE_used'
                        
                        subprocess.Popen(f'$ANTs_registration -d 3 -n 4 -f {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz -m {sub_ses_directory}/{mprage} -t r -o {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_used', shell=True).wait()
                        
                        # self.client.containers.run('antsx/ants', auto_remove=True, volumes=[f'{sub_ses_derivative_path_transfo}:/data', f'{sub_ses_directory}:/media'], command=register)
                        
                        # Change the name of registration output
                        shutil.move(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_usedWarped.nii.gz'), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz'))
                    
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
                    #convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz'
                    
                    subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
                    #convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.mgz'
                    
                    subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.mgz', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
                 
                    
                    # https://surfer.nmr.mgh.harvard.edu/fswiki/Samseg
                    #samseg = f'run_samseg -i /input/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.mgz -i /input/sub-{self.sub}_FLAIR_used.mgz --lesion --lesion-mask-pattern 0 1 --threads 4 -o /media --save-posteriors'
                    self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = [f'{sub_ses_derivative_path_segment}/SAMSEG_results'])
                    subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.mgz -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz --lesion --lesion-mask-pattern 0 1 --threads 4 -o {sub_ses_derivative_path_segment}/SAMSEG_results --save-posteriors', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/input', f'{sub_ses_derivative_path_segment}:/media'],command=samseg)
                    #subprocess.Popen(f'docker run --rm -e FS_LICENSE=/data/license.txt -v {license_location}:/data -v {sub_ses_derivative_path_transfo}:/input -v {sub_ses_derivative_path_segment}:/media freesurfer/freesurfer:7.2.0 {samseg}', shell=True).wait()
                    
                    #convert = f'mri_convert /usr/local/freesurfer/subjects/posteriors/Lesions.mgz /usr/local/freesurfer/subjects/sub-{self.sub}_lesions.nii.gz'
                    
                    subprocess.Popen(f'mri_convert {sub_ses_derivative_path_segment}/SAMSEG_results/posteriors/Lesions.mgz {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz', shell=True).wait()
                    
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
                    #convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz'
                    
                    subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
                    # convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_MPRAGE_used.nii.gz /usr/local/freesurfer/subjects/sub-{self.sub}_MPRAGE_used.mgz'
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
                 
                    
                    # https://surfer.nmr.mgh.harvard.edu/fswiki/Samseg
                    # samseg = f'run_samseg -i /input/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o /media --save-posteriors'
                    self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = [f'{sub_ses_derivative_path_segment}/SAMSEG_results'])
                    subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o {sub_ses_derivative_path_segment}/SAMSEG_results --save-posteriors', shell=True).wait()
                   
                    # subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o {sub_ses_derivative_path_segment} --save-posteriors', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/input', f'sub_ses_derivative_path_segment:/media'],command=samseg)
                    #subprocess.Popen(f'docker run --rm -e FS_LICENSE=/data/license.txt -v {license_location}:/data -v {sub_ses_derivative_path_transfo}:/input -v {sub_ses_derivative_path_segment}:/media freesurfer/freesurfer:7.2.0 {samseg}', shell=True).wait()
                    
                    # convert = f'mri_convert /usr/local/freesurfer/subjects/posteriors/Lesions.mgz /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz'
                    
                    subprocess.Popen(f'mri_convert {sub_ses_derivative_path_segment}/SAMSEG_result/posteriors/Lesions.mgz {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz', shell=True).wait()
                    
                    # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_segment}:/usr/local/freesurfer/subjects'], command=convert)
              
              
           
        
                # Change the name of segmentation output
                #shutil.move(pjoin(sub_ses_derivative_path_segment, f'seg.mgz'), pjoin(sub_ses_derivative_path_segment, f'sub{self.sub}_lesions.mgz'))
                except Exception as e:
                    print(f'Error {e} while running Samseg for sub-{self.sub}_ses{self.ses}!')
             
            #Binarizing the lesion probability  mask     
            try:
                logging.info(f'Binarizing lesion probability mask for sub-{self.sub} ses-{self.ses}...')
               
                threshold = 0.5
                image = nib.load(f'{sub_ses_derivative_path_segment}/SAMSEG_results/posteriors/Lesions.mgz')
                lesions = image.get_fdata()
                lesions[lesions >= threshold] = 1
                lesions[lesions < threshold] = 0
            
                nifti_out = nib.Nifti1Image(lesions, affine=image.affine)
                # nib.save(nifti_out, f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz')
                
            except Exception as e:
                print(f'Error {e} while binarizing lesion probability mask for sub-{self.sub}_ses{self.ses}!')
                
            print('end SAMSEG')
               
      
        
        if self.recon_all:
            #print("debug: recon-all begin")
            self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories=directory_fs_sub_ses)
            subprocess.Popen(f'recon-all -all -i {sub_ses_directory}/{mprage} -subjid sub-{self.sub}_ses-{self.ses}_MPRAGE -sd {sub_ses_fs_path}', shell=True).wait()
        
        if self.step3 == True:
            print('step 3')  
            
            self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories=[pjoin(self.bids.root_dir, 'derivatives', derivative), pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}'), pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}'), pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg), sub_ses_derivative_path_stats])
            
            # # Prend un des produits de recon-all et le reconvertit en nii.gz pour la suite
            # print(f'step 3.1 : Transform the Freesurfer segmentation (product of recon-all) into the normalized space (Samseg space)')
            # try:
            #     logging.info(f'mri/orig.mgz --> mri/orig.nii.gz and mri/aseg.mgz --> mri.aseg.nii.gz')
                
            #     subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.mgz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz', shell=True).wait()
            #     subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.mgz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz', shell=True).wait()

            # except Exception as e:
            #     print(f'Error {e} while converting mri/orig.mgz --> mri/orig.nii.gz and/or mri/aseg.mgz --> mri.aseg.nii.gz')

                        
            # try:
            #     logging.info(f'Registration Orig on MPRAGE_used')
                
            #     subprocess.Popen(f'$ANTs_registration -d 3 -n 4 -f {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz -m {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -t r -o {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_used', shell=True).wait()

                
            # except Exception as e:
            #     print(f'Error {e} while registrating Orig on MPRAGE_used')
                
            
            # try:
            #     logging.info(f'Registration aseg on MPRAGE_used')
                
            #     #https://manpages.ubuntu.com/manpages/bionic/man1/antsApplyTransforms.1.html
                
            #     subprocess.Popen(f'$ANTSPATH/antsApplyTransforms -d 3 -i {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz -r {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz -n GenericLabel -t {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_used0GenericAffine.mat -o {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg_used.nii.gz', shell=True).wait()
                
            # except Exception as e:
            #     print(f'Error {e} while registrating aseg on MPRAGE_used')
                
            # print(f'step 3.2 : Transform de binarized lesion mask (product of Samseg) into freesurfer space')
            
            
            # try:
            #     logging.info(f'Transforming the binarized lesion mask (product of Samseg) into freesurfer space')
                
            #     subprocess.Popen(f'$ANTSPATH/antsApplyTransforms -d 3 -i {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz -r {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -n GenericLabel -t [{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_used0GenericAffine.mat, 1] -o {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz', shell=True).wait()
            #     subprocess.Popen(f'$ANTSPATH/antsApplyTransforms -d 3 -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz -r {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -n GenericLabel -t [{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_used0GenericAffine.mat, 1] -o {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.nii.gz', shell=True).wait()
                
            #     subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.mgz', shell=True).wait()
            #     subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.nii.gz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.mgz', shell=True).wait()

            # except Exception as e:
            #     print(f'Error {e} while transforming the binarized lesion mask (product of Samseg) into freesurfer space')
            
            
            print(f'step 3.3 : Merge the brain segmentation files with the lesion masks in both samseg and Freesurfer spaces')
            
            def update_aseg_norm(subject, path):
                """
                Merge normalized Freesurfer brain segmentation with the lesion segmentation 
                performed by samseg. 
                Parameters
                ----------
                subject : TYPE str
                    Subject id.
                Returns
                -------
                None.
                """      
                # Load lesion mask
                lesion_image = nib.load(f'{path}/sub-{subject}_ses-{self.ses}_lesions_binary.nii.gz')
                lesion_mx = lesion_image.get_fdata()
                
                lesion_mask = ma.masked_not_equal(lesion_mx,1)

                # Load Freesurfer segmentation mask (aseg)
                aseg_image = nib.load(f'{path}/sub-{subject}_ses-{self.ses}_aseg_used.nii.gz')
                aseg_mx = aseg_image.get_fdata()
                
                # Set all voxels of aseg marked as lesion in the lesion mask to 99 (Freesurfer lesion id)
                aseg_mask = ma.masked_array(aseg_mx, np.logical_not(lesion_mask.mask), fill_value=99).filled()


                # Save resulting matrix to nifti file
                nifti_out = nib.Nifti1Image(aseg_mask, affine=aseg_image.affine)

                # nifti_out_2 = nib.Nifti1Image(nifti_out, affine=aseg_image.affine, header=aseg_image.header)
                # nib.save(nifti_out, f'{path}/sub-{subject}_ses-{self.ses}_aseg_lesions.nii.gz')
                # nifti_out.to_filename(f'{path}/sub-{subject}_aseg_lesions.nii.gz')
                
            def update_aseg_fs(subject, path):
                
                """
                Merge Freesurfer brain segmentation with the lesion segmentation 
                performed by samseg in Freesurfer's space.
                Parameters
                ----------
                subject : TYPE str
                    Subject id.
                Returns
                -------
                None.
                """
                
                # Load lesion mask
                lesion_image = nib.load(f'{path}/sub-{subject}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz')
                lesion_mx = lesion_image.get_fdata()
                
                lesion_mask = ma.masked_not_equal(lesion_mx,1)
                
                # Loa Freesurfer segmentation mask (aseg)
                aseg_image = nib.load(f'{path}/sub-{subject}_ses-{self.ses}_MPRAGE/mri/aseg.mgz')
                aseg_mx = aseg_image.get_fdata()
                
                # Set all voxels of aseg marked as lesion in the lesion ask to 99 (Freesurfer lesion id)
                aseg_mask = ma.masked_array(aseg_mx, np.logical_not(lesion_mask.mask), fill_value=99).filled()
                
                # Save resulting matrix to nifti file
                nifti_out = nib.Nifti1Image(aseg_mask, affine=aseg_image.affine)
                # nib.save(nifti_out, f'{path}/sub-{subject}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz')

            
            
            def update_aseg(subject, path_fs, path_norm):
                """
                Updates aseg in Freesurfer space as well as in Samseg space according to the lesion mask
                created by samseg and then binarized.
                Parameters
                ----------
                subject : TYPE str
                    Subject id.
                Returns
                -------
                None.
                """
                update_aseg_norm(subject, path_norm)
                update_aseg_fs(subject, path_fs)
                
            # Step 3.3
            try:
                update_aseg(self.sub, sub_ses_fs_path, sub_ses_derivative_path_segment)
            except Exception as e:
                print(e)
            
            
            print(f'step 3.4 : Lesion labelling, volumetry and location')
            
            WHITE_MATTER   = 2
            GRAY_MATTER    = 3
            VENTRICLES     = 4
            INFRATENTORIAL = 16 
            
            def load_segmentations(subject):
                """
                Loads the segmentation image and matrix as well as the lesion matrix
                Parameters
                ----------
                subject : TYPE <str>
                    Subject id.
                Returns
                -------
                aseg_image : TYPE <nibabel.freesurfer.mghformat.MGHImage>
                    Image of the Freesurfer segmentation mask.
                seg:         TYPE 3D numpy.ndarray
                    Matrix of segmentations.
                lesion:      TYPE 3D numpy.ndarray
                    Lesion matrix.
                """
                # Load segmentations
                aseg_img = nib.load(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg_lesions.nii.gz')
                seg = aseg_img.get_fdata()
                
                # Make lesion matrix from segmentations matrix
                lesion = seg.copy()
                lesion[lesion!=99] = 0
                lesion[lesion==99] = 1
                
                return aseg_img, seg, lesion
            
            
            
            
            
            def make_lesions_csv(subject, minimum_lesion_size=5):
                """
                Makes the lesion based database (lesions.csv) that regroups informations about
                the lesions of one subject (label - volume - location). 
                Parameters
                ----------
                subject : TYPE <str>
                    Subject id.
                minimum_lesion_size : TYPE <int>, optional
                    Minimum size for a lesion to be considered as such. The default is 5.
                Returns
                -------
                None.
                """
                # Load segmentations
                image, aseg, lesion = load_segmentations(subject) 
                
                # Get number of components (thus number of lesions)
                structure = np.ones((3, 3, 3))
                labeled_lesions, nlesions = label(lesion,structure)
                
                print("Number of lesions before discarding: {0}".format(nlesions))
                
                id_lesions_dic = {}
                            
                # For every lesion
                for lesion_id in range(1,nlesions+1):
                    # Create lesion mask for this specific lesion
                    lesions_mskd = ma.masked_where(labeled_lesions != lesion_id, labeled_lesions)
                    
                    # Compute the lesion volume
                    lesion_voxel_volume_count = lesions_mskd.sum() // lesion_id
                    
                    
                    if lesion_voxel_volume_count > minimum_lesion_size:
                        print("\n\nLesion {0}: {1} voxels".format(lesion_id, lesion_voxel_volume_count))
                        
                        # Get the lesion location
                        loc_20,_,_ = lesion_location(subject, lesion_id, lesion_mx=labeled_lesions,
                                                   aseg_mx=aseg, percentage=0.2)
                        # loc_30,_,_ = lesion_location(subject, lesion_id, lesion_mx=labeled_lesions,
                        #                            aseg_mx=aseg, percentage=0.3)
                        
                        id_lesions_dic[lesion_id] = [lesion_id, lesion_voxel_volume_count, loc_20] #, loc_30]#, loc_40, loc_50]
                        
                    else: 
                        # Discard lesion if size is inferior to the minimum lesion size
                        print("\n\nLesion {0}: {1} voxels ==> Discarded (too small)".format(lesion_id, lesion_voxel_volume_count))
                        #labeled_lesions[labeled_lesions == lesion_id] = 0 # Leave commented, not working
                
                # Make the database
                columns = ["lesion_id", "Voxel Volume", "Location"] #" 20%", "Location 30%"]
                
                df = pd.DataFrame.from_dict(id_lesions_dic, orient='index', columns=columns)
                # df.to_csv(pjoin(sub_ses_derivative_path_stats, f'sub-{self.sub}_ses-{self.ses}_lesions.csv'), index=False)
                
                # print("debug: bruh")
                
                # bruh = nib.Nifti1Image(np.zeros(256,256,256))
                # nib.save(bruh, pjoin(sub_ses_derivative_path_segment, f'bruh.nii.gz'))
                
                
                # Save the lesion mask with labels to a nifti file
                nifti_out = nib.Nifti1Image(labeled_lesions, affine=image.affine, header=image.header)
                # nifti_out = image.__class__(labeled_lesions, affine=image.affine, header=image.header)
                # nib.save(nifti_out, pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_labeled_lesions.nii.gz'))
                
                
                
                
            def lesion_location(subject, lesion_label, lesion_mx=None, aseg_mx=None, percentage=0.2):
                """
                Finds the location of a lesion
                Parameters
                ----------
                subject : TYPE <str>
                    Subject id.
                lesion_label : TYPE <int>
                    Label id for the lesion of interest.
                lesion_mx : TYPE 3D numpy.ndarray, optional
                    Matrix of labeled lesions. The default is retrieved based on the machine and subject path.
                aseg_mx : TYPE 3D numpy.ndarray, optional
                    Matrix of labeled brain structures. The default is retrieved based on the machine and subject path.
                percentage : TYPE <int>, optional
                    Percentage of the lesion volume that has to match with the dilated brain structure. The default is 0.2.
                Returns
                -------
                TYPE <str>
                    Lesion location. Either "White Matter", "Cortical or juxta-cortical", "Periventricular" or "Infratentorial".
                lesion_volume : TYPE <int>
                    Lesion volume (voxel count).
                """
                
                if lesion_mx is None:
                    # Load lesion mask
                    lesion_image = nib.load(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_labeled_lesions.nii.gz')
                    lesion_mx = lesion_image.get_fdata()
                    
                if aseg_mx is None:
                    # Load segmentation
                    aseg_image = nib.load(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg.mgz')
                    aseg_mx = aseg_image.get_fdata()
                
                
                # Regroup left and right structures into the same label 
                aseg_mx[aseg_mx == 41] = WHITE_MATTER #White matter
                aseg_mx[aseg_mx == 42] = GRAY_MATTER #Gray matter
                aseg_mx[aseg_mx == 43] = VENTRICLES #Ventricle
                aseg_mx[aseg_mx == 7]  = INFRATENTORIAL #Left Cerebellum Cortex -> Brainstem
                aseg_mx[aseg_mx == 8]  = INFRATENTORIAL #Left Cerebellum WM -> Brainstem
                aseg_mx[aseg_mx == 47] = INFRATENTORIAL #Right Cerebellum Cortex -> Brainstem
                aseg_mx[aseg_mx == 46] = INFRATENTORIAL #Right Cerebellum WM -> Brainstem
                
                results = []
                dic = {WHITE_MATTER: "white matter", GRAY_MATTER: "gray matter", 
                       VENTRICLES: "ventricles", INFRATENTORIAL: "infratentorial structures"}
                
                for seg,iterations in [(GRAY_MATTER, 1), (VENTRICLES, 3), (INFRATENTORIAL, 1)]:
                    
                    print("Dilating " + dic[seg] + "...", end= " ")
                    
                    # Make the brain structure segmentation mask (other segmentations removed)
                    aseg_mask = ma.masked_not_equal(aseg_mx, seg)
                    aseg_mask.fill_value = 0
                    aseg_mask = aseg_mask.filled()
                    
                    # Dilate the brain structure 'iterations' timesaseg_temp 
                    aseg_temp = binary_dilation(aseg_mask, iterations=iterations).astype(aseg_mx.dtype) # Binary mask
                    
                    # Append the results
                    try:
                        matching_voxels = count_matching_lesion_voxels(lesion_mx, aseg_temp, lesion_label, seg)
                    except Exception as e:
                        print(f'DEBUG: error {e}')
                    print( str(matching_voxels) + " voxels in common with the lesion")
                    results.append(matching_voxels)
                
                # Get the lesion volume
                lesions_mskd = ma.masked_where(lesion_mx != lesion_label, lesion_mx)
                lesion_volume = lesions_mskd.sum() // lesion_label
                
                index = {-1:"White Matter", 0:"Cortical or juxta-cortical", 1:"Periventricular", 2: "Infratentorial"}
                
                # Set the lesion location as white matter if the count of overlapping voxels do not 
                # exceed the percentage of the lesion volume
                loc = results.index(max(results))
                if (loc == 0 or loc == 1) and max(results) < percentage*lesion_volume:
                    loc = -1
                
                return index[loc], lesion_volume, results
                 
            
            def count_matching_lesion_voxels(lesion_mx, segmentation_mx, lesion, segmentation):
                """
                Counts the number of voxels where 
                    lesion_mx[index]       = lesion         and 
                    segmentation_mx[index] = segmentation 
                for the same index
                Parameters
                ----------
                lesion_mx : 3D numpy.ndarray
                    Matrix of labeled lesions.
                segmentation_mx : 3D numpy.ndarray
                    Matrix of labeled brain segmentation.
                lesion : TYPE <int>
                    Label for the lesion of interest.
                segmentation : TYPE <int>
                    Label for the brain structure of interest.
                Returns
                -------
                TYPE <int>
                    Count of matching voxels.
                """
                
                
                les_mx = lesion_mx.copy()
                
                # Set all voxels whose value differ from the lesion id to -1
                les_mx = ma.masked_not_equal(les_mx, lesion)
                les_mx.fill_value = -1
                les_mx = les_mx.filled()
                
                # Set all voxels whose value equal to the lesion id to 1
                les_mx[les_mx == lesion] = 1
                
                return np.sum(les_mx == segmentation_mx)   
                
                
                
                
                
            def make_location_mask(subject, percentage=20):
                """
                Makes a lesion location mask based on the lesion based db (lesions.csv)
                Parameters
                ----------
                subject : TYPE <str>
                    Subject id.
                percentage : TYPE <int>, optional
                    Percentage of the lesion volume that has to match with the dilated brain 
                    structure. The default is 20.
                Returns
                -------
                None.
                """
                # Retrieve lesion based database
                df = pd.read_csv(f'{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}_lesions.csv')
                locations = list(df["Location"]) # {0}%".format(percentage)])
                ids = list(df["lesion_id"])
                
                lesion_image = nib.load(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_labeled_lesions.nii.gz')
                lesion_mx = lesion_image.get_fdata()
                
                lesion_loc = lesion_mx.copy()
                
                dictionary = {"White Matter":100, "Cortical or juxta-cortical":200, "Periventricular":300, "Infratentorial":400}
                
                for i in range(len(locations)):
                    lesion_loc[lesion_loc == ids[i]] = dictionary[locations[i]]
                
                nifti_out = nib.Nifti1Image(lesion_loc, affine=lesion_image.affine, header=lesion_image.header)
                # nib.save(nifti_out, f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesion_locations.nii.gz')
            
                
                
                
                
            # Step 3.4 
            make_lesions_csv(self.sub)
            print('make_location_mask')
            make_location_mask(self.sub, 20)
            
            
            print('Step 3.5 : Recompute Freesurfer volumetry based on the new segmentation file')
            
            
            try:
                logging.info(f'Converting mri/aseg_lesions.nii.gz --> mri/aseg_lesion.mgz to use it in freesurfer ')
                
                subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz', shell=True).wait()
                shutil.copy(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz', f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg_lesions.nii.gz')

            except Exception as e:
                print(f'Error {e} while converting mri/aseg_lesions.nii.gz --> mri/aseg_lesion.mgz')
                
            try:
              logging.info(f'Executing mri_segstats on aseg_lesion.mgz')
              
              subprocess.Popen(f'mri_segstats --seed 1234 --seg {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz \
                               --sum {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats --pv {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz \
                                 --empty --brainmask {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/brainmask.mgz --brain-vol-from-seg --excludeid 0 \
                                   --excl-ctxgmwm --supratent --subcortgray --in {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz \
                                     --in-intensity-name norm --in-intensity-units MR --etiv --surf-wm-vol --surf-ctx-vol \
                                       --totalgray --euler --ctab \
                                         /home/stluc/Programmes/freesurfer/ASegStatsLUT.txt --sd {sub_ses_fs_path} --subject sub-{self.sub}_ses-{self.ses}_MPRAGE', shell=True).wait()

            except Exception as e:
              print(f'Error {e} while Executing mri_segstats on aseg_lesion.mgz')
              
            print(f'Step 3.6 : Make subject-{self.sub}_ses-{self.ses}.csv')            
            
            def get_brain_volumes(subject):
                """
                Retrieves brain volumes from the aseg_lesions.stats file produced by volumetry.sh
                Parameters
                ----------
                subject : TYPE <str>
                    Subject id.
                Returns
                -------
                stats : TYPE <dict>
                    Dictionary of brain volumes.
                """
                stats={}
                
                with open(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats') as file:
                    for line in file:
                        if "Estimated Total Intracranial Volume," in line:
                            lst = line.split(', ')
                            stats['Intracranial volume'] = float(lst[3])
                        elif "Brain Segmentation Volume," in line:
                            lst = line.split(', ')
                            stats['Brain volume'] = float(lst[3])
                        elif "Volume of ventricles and choroid plexus," in line:
                            lst = line.split(', ')
                            stats['Ventricles'] = float(lst[3])
                        elif "Total gray matter volume," in line:
                            lst = line.split(', ')
                            stats['Gray matter'] = float(lst[3])
                        elif "Total cerebral white matter volume," in line:
                            lst = line.split(', ')
                            stats['White matter'] = float(lst[3])
                        elif "Left-Caudate" in line:
                            lst = line.split(' ')
                            column = 0
                            for el in lst:
                                if el != '':
                                    if column == 5:
                                        left_caudate = float(el)
                                    column+=1
                        elif "Right-Caudate" in line:
                            lst = line.split(' ')
                            column = 0
                            for el in lst:
                                if el != '':
                                    if column == 5:
                                        right_caudate = float(el)
                                    column+=1
                        elif "Left-Putamen" in line:
                            lst = line.split(' ')
                            column = 0
                            for el in lst:
                                if el != '':
                                    if column == 5:
                                        left_putamen = float(el)
                                    column+=1
                        elif "Right-Putamen" in line:
                            lst = line.split(' ')
                            column = 0
                            for el in lst:
                                if el != '':
                                    if column == 5:
                                        right_putamen = float(el)
                                    column+=1
                        elif "Left-Thalamus" in line:
                            lst = line.split(' ')
                            column = 0
                            for el in lst:
                                if el != '':
                                    if column == 5:
                                        left_thalamus = float(el)
                                    column+=1
                        elif "Right-Thalamus" in line:
                            lst = line.split(' ')
                            column = 0
                            for el in lst:
                                if el != '':
                                    if column == 5:
                                        right_thalamus = float(el)
                                    column+=1
                        elif " WM-hypointensities" in line:
                            lst = line.split(' ')
                            column = 0
                            for el in lst:
                                if el != '':
                                    if column == 5:
                                        wm_hypo = float(el)
                                    column+=1
                    
                    stats['Caudate']=left_caudate+right_caudate
                    stats['Putamen']=left_putamen+right_putamen
                    stats['Thalamus']=left_thalamus+right_thalamus
                    stats['WM-hypointenisities'] = wm_hypo
                    
                    brainvol = stats["Intracranial volume"]
                    for key,value in stats.items():
                        if key != "Intracranial volume":
                            stats[key] = value/brainvol
                   
                    
                    return stats
                
                
            def get_lesions_information(subject, stats):
                """
                Updates stats with the subjects' lesion informations
                Parameters
                ----------
                subject : TYPE <str>
                    Subject id.
                stats : TYPE <dict>
                    Dictionary of brain volumes.
                Returns
                -------
                stats : TYPE <dict>
                    Dictionary of brain volumes and lesion informations.
                wm_lesions: TYPE <int>
                    Total volume of white matter lesions
                """
                
                df = pd.read_csv(f'{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}_lesions.csv')
                
                lesion_count  = df['lesion_id'].count()
                lesion_volume = df['Voxel Volume'].sum()
                
                stats["Number of lesions"]   = lesion_count
                stats["Total lesion volume"] = lesion_volume
                
                wm_lesions = df[df['Location'] != 'Infratentorial']['Voxel Volume'].sum()
                
                wml = df[df["Location"] == 'White Matter']['Voxel Volume'].sum()
                peril = df[df["Location"] == 'Periventricular']['Voxel Volume'].sum()
                gml = df[df["Location"] == 'Cortical or juxta-cortical']['Voxel Volume'].sum()
                infratl = df[df["Location"] == 'Infratentorial']['Voxel Volume'].sum()
                
                stats['White matter lesions %'] = (wml / lesion_volume)*100
                stats['Cortical or juxta-cortical lesions %'] = (gml / lesion_volume)*100
                stats['Periventricular lesions %'] = (peril / lesion_volume)*100
                stats['Infratentorial lesions %'] = (infratl / lesion_volume)*100
                
                
                
                return stats, wm_lesions
                
                
            
            def make_subject_csv(subject):
                
                stats = get_brain_volumes(subject)
                stats, wm_lesions = get_lesions_information(subject,stats)
                
                ic_volume = stats['Intracranial volume']
                
                stats['White matter'] = stats['White matter'] + stats['WM-hypointenisities'] 
                stats['Total lesion volume'] = stats['Total lesion volume'] / ic_volume 
                
                df = pd.DataFrame.from_dict(stats, orient='index', columns = [subject])
                df = df.transpose()
                # df.to_csv(f'{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}.csv')
                
            # Step 3.6 
            make_subject_csv(self.sub)
                    
        print('LesVolLoc end')
            




# # =============================================================================
# # LesVolocSegWorker
# # =============================================================================
# class LesVoLocSegWorker(QObject):
#     finished = pyqtSignal()
#     progress = pyqtSignal(int)

#     def __init__(self, bids, sub, ses, normalization, mprage, step1, step2, recon_all, step3):
#         """
        
        
#         Parameters
#         ----------
#         bids : TYPE
#           DESCRIPTION.
#         sub : TYPE
#           DESCRIPTION.
#         ses : TYPE
#           DESCRIPTION.
#         normalization : TYPE #True to decrease images resolution
#           DESCRIPTION.
#         mprage : TYPE        #True if mprage available
#           DESCRIPTION.
#         step1 : TYPE         #True to execute the preprocessing part
#           DESCRIPTION.
#         step2 : TYPE         #True to execute SAMSEG segmentation: Produce lesion probability mask
#           DESCRIPTION.
#         step3 : TYPE         #True to binarize the lesion probability mask
#           DESCRIPTION.
        
#         Returns
#         -------
#         None.
        
#         """
#         super().__init__()
#         self.bids = bids
#         self.sub = sub
#         self.ses = ses
#         self.normalization = normalization 
#         self.mprage = mprage               
#         self.step1 = step1                 
#         self.step2 = step2 
#         self.recon_all = recon_all
#         self.step3 = step3      
#         print(f'{normalization=}')
#         print(f'{mprage=}')
#         print(f'{step1=}')
#         print(f'{step2=}')
#         self.client = docker.from_env()
      
  
#     def run(self): 
        
#         # Define the directories for a certain SUBJECT and SESSION
#         fs = 'FreeSurfer'
#         derivative = 'LesVolLoc'
#         samseg = 'SAMSEG'
#         segment = 'segmentation'
#         transfo = 'transformation'
#         sub_ses_directory = pjoin(self.bids.root_dir, f'sub-{self.sub}', f'ses-{self.ses}', 'anat')
#         flair = f'sub-{self.sub}_ses-{self.ses}_FLAIR.nii.gz'
#         mprage = f'sub-{self.sub}_ses-{self.ses}_acq-MPRAGE_T1w.nii.gz'
#         # license_location = f'/home/stluc/Programmes/freesurfer'
#         #create directories
#         directorysegment = [pjoin('derivatives', derivative), pjoin('derivatives', derivative, samseg), pjoin('derivatives', derivative, samseg, segment), pjoin('derivatives', derivative, samseg, segment, f'sub-{self.sub}'), pjoin('derivatives', derivative, samseg, segment, f'sub-{self.sub}', f'ses-{self.ses}')]
#         directorytransfo = [pjoin('derivatives', derivative), pjoin('derivatives', derivative, samseg), pjoin('derivatives', derivative, samseg, transfo), pjoin('derivatives', derivative, samseg, transfo, f'sub-{self.sub}'), pjoin('derivatives', derivative, samseg, transfo, f'sub-{self.sub}', f'ses-{self.ses}')]
        
#         self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = directorysegment)
#         self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = directorytransfo)
#         sub_ses_derivative_path_segment = pjoin(self.bids.root_dir, 'derivatives', derivative, samseg, segment, f'sub-{self.sub}', f'ses-{self.ses}')
#         sub_ses_derivative_path_transfo = pjoin(self.bids.root_dir, 'derivatives', derivative, samseg, transfo, f'sub-{self.sub}', f'ses-{self.ses}')
#         sub_ses_derivative_path_stats = pjoin(self.bids.root_dir, 'derivatives', derivative, samseg, 'stats', f'sub-{self.sub}', f'ses-{self.ses}')
#         #dossier dans lequel on est sense mettre les resultats de recon-all de fs
#         directory_fs_sub_ses = [pjoin('derivatives', derivative), pjoin(self.bids.root_dir, 'derivatives', derivative, fs), pjoin(self.bids.root_dir, 'derivatives', derivative, fs, f'sub-{self.sub}'), pjoin(self.bids.root_dir, 'derivatives', derivative, fs, f'sub-{self.sub}', f'ses-{self.ses}')]
#         sub_ses_fs_path = pjoin(self.bids.root_dir, 'derivatives', derivative, fs, f'sub-{self.sub}', f'ses-{self.ses}')
          
#         #Perform Segmentation with SAMSEG step by step
        
#         #Step1 : Preprocessing (normalization and registration FLAIR and MPRAGE)
#         if self.step1 == True: 
            
#             print('step1')
          
#             if self.normalization == True:
#                 print('normalization')
              
#                 # #Pas encore possible de gérer a cause des autorisations
#                 # #Faut renommer le dossier manuellement et trouver comment le supprimer
#                 # #Remove existing file that will be recomputed in the directory
#                 if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_used')):
#                     shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_used'))
#                 if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz')):
#                     shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz'))
                          
#                 # # Resize FLAIR to have 256x256x256, 1mm3
#                 try:
#                     logging.info(f'Resizing FLAIR for sub-{self.sub} ses-{self.ses}...')
                    
#                     # a la sortie de motioncor --> ce qui nous intéresse c'est le fichier orig.mgz qui est dans
#                     # sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_used/mri
#                     # /usr/local/freesurfer/subjects
#                     #resize = f'recon-all -motioncor -i /input/{flair} -subjid sub-{self.sub}_ses-{self.ses}_FLAIR_used -sd /usr/local/freesurfer/subjects'
                    
#                     subprocess.Popen(f'recon-all -motioncor -i {sub_ses_directory}/{flair} -subjid sub-{self.sub}_ses-{self.ses}_FLAIR_used -sd {sub_ses_derivative_path_transfo}', shell=True).wait()
                    
#                     # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data',f'{sub_ses_directory}:/input', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects' ], command=resize)
#                     #subprocess.Popen(f'docker run --rm -e FS_LICENSE=/data/license.txt -v {license_location}:/data -v {sub_ses_directory}:/input -v {sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects freesurfer/freesurfer:7.2.0 {resize}', shell=True).wait()
#                     #print(f'docker run --rm -e FS_LICENSE=/data/license.txt -v {license_location}:/data -v {sub_ses_directory}:/input -v {sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects freesurfer/freesurfer:7.2.0 {resize}')
                    
#                 except Exception as e:
#                     print(f'Error {e} when resizing FLAIR for sub-{self.sub}_ses-{self.ses}!')
                
#                 # Convert mgz file from freesurfer to nii file 
#                 try:
#                     logging.info(f'Converting FLAIR_used.mgz to .nii.gz for sub-{self.sub} ses-{self.ses}...')
                     
#                     #convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_FLAIR_used/mri/orig.mgz /usr/local/freesurfer/subjects/sub-{self.sub}_FLAIR_used.nii.gz'
#                     #3eme path vers l'endroit où se trouve la license
                    
#                     subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used/mri/orig.mgz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz', shell=True).wait()
                    
#                     # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True,environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
                 
#                 except Exception as e:
#                     logging.info(f'Error {e} when converting FLAIR_used.mgz to .nii.gz for sub-{self.sub}_ses{self.ses}!')
                     
#                 # Register MPRAGE on FLAIR 
#                 if self.mprage == True:
#                     print('step1 mprage')
#                     try:
#                         logging.info(f'Registration of MPRAGE on FLAIR_used for sub-{self.sub} ses-{self.ses}...')
                         
#                         #register = f'/opt/ants/bin/antsRegistrationSyNQuick.sh -d 3 -n 4 -f /data/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz -m /media/{mprage} -t r -o sub-{self.sub}_ses-{self.ses}_MPRAGE_used'
                        
#                         subprocess.Popen(f'$ANTs_registration -d 3 -n 4 -f {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz -m {sub_ses_directory}/{mprage} -t r -o {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_used', shell=True).wait()
                        
#                         # self.client.containers.run('antsx/ants', auto_remove=True, volumes=[f'{sub_ses_derivative_path_transfo}:/data', f'{sub_ses_directory}:/media'], command=register)
                     
#                         # Change the name of registration output
#                         shutil.move(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_usedWarped.nii.gz'), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz'))
                    
#                     except Exception as e:
#                         logging.error(f'Error {e} during registration of MPRAGE on FLAIR_used for sub-{self.sub}_ses{self.ses}!')
                   
#                     #PAs encore utilise    
#             else: #pas de resize -> juste registration de MPRAGE sur FLAIR  
            
#                 print('no normalization')
            
#                 if self.mprage == True:
#                     print('no normalization mprage')
              
#                     try:
#                         logging.info(f'Registration of MPRAGE on FLAIR_used for sub-{self.sub} ses-{self.ses}...')
                        
#                         #Remove existing file that will be recomputed in the directory
#                         #os.remove(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_FLAIR_used.nii.gz'))
#                         #os.remove(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_MPRAGE_used.nii.gz'))
#                         if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_used')):
#                             shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_used'))
#                         if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz')):
#                             shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz'))
                      
#                         #Copy FLAIR in directory of transformations for access simplicity
#                         shutil.copyfile(pjoin(sub_ses_directory, flair), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz'))
                        
#                         #register = f'/opt/ants/bin/antsRegistrationSyNQuick.sh -d 3 -n 4 -f /data/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz -m /media/{mprage} -t r -o sub-{self.sub}_ses-{self.ses}_MPRAGE_used'
                        
#                         subprocess.Popen(f'$ANTs_registration -d 3 -n 4 -f {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz -m {sub_ses_directory}/{mprage} -t r -o {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_used', shell=True).wait()
                        
#                         # self.client.containers.run('antsx/ants', auto_remove=True, volumes=[f'{sub_ses_derivative_path_transfo}:/data', f'{sub_ses_directory}:/media'], command=register)
                        
#                         # Change the name of registration output
#                         shutil.move(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_usedWarped.nii.gz'), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz'))
                    
#                     except Exception as e:
#                         print(f'Error {e} during registration of MPRAGE on FLAIR_used for sub-{self.sub}_ses{self.ses}!')
                
                
#         # Step2 : Segmentation using SAMSEG to compute lesion probability mask
#         if self.step2 == True:
#             print('step 2')
            
#             if self.mprage == True:
#                 print('step2 mprage')
#                 try:
#                     logging.info(f'Running Samseg for sub-{self.sub} ses-{self.ses}...')
                    
#                     #mri_convert pour avoir les FLAIR et MPRAGE_used en mgz au bon endroit
#                     #convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz'
                    
#                     subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz', shell=True).wait()
                    
#                     # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
#                     #convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.mgz'
                    
#                     subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.mgz', shell=True).wait()
                    
#                     # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
                 
                    
#                     # https://surfer.nmr.mgh.harvard.edu/fswiki/Samseg
#                     #samseg = f'run_samseg -i /input/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.mgz -i /input/sub-{self.sub}_FLAIR_used.mgz --lesion --lesion-mask-pattern 0 1 --threads 4 -o /media --save-posteriors'
#                     self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = [f'{sub_ses_derivative_path_segment}/SAMSEG_results'])
#                     subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.mgz -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz --lesion --lesion-mask-pattern 0 1 --threads 4 -o {sub_ses_derivative_path_segment}/SAMSEG_results --save-posteriors', shell=True).wait()
                    
#                     # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/input', f'{sub_ses_derivative_path_segment}:/media'],command=samseg)
#                     #subprocess.Popen(f'docker run --rm -e FS_LICENSE=/data/license.txt -v {license_location}:/data -v {sub_ses_derivative_path_transfo}:/input -v {sub_ses_derivative_path_segment}:/media freesurfer/freesurfer:7.2.0 {samseg}', shell=True).wait()
                    
#                     #convert = f'mri_convert /usr/local/freesurfer/subjects/posteriors/Lesions.mgz /usr/local/freesurfer/subjects/sub-{self.sub}_lesions.nii.gz'
                    
#                     subprocess.Popen(f'mri_convert {sub_ses_derivative_path_segment}/SAMSEG_results/posteriors/Lesions.mgz {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz', shell=True).wait()
                    
#                     # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_segment}:/usr/local/freesurfer/subjects'], command=convert)
                  
                  
               
            
#                 # Change the name of segmentation output
#                 #shutil.move(pjoin(sub_ses_derivative_path_segment, f'seg.mgz'), pjoin(sub_ses_derivative_path_segment, f'sub{self.sub}_lesions.mgz'))
#                 except Exception as e:
#                     print(f'Error {e} while running Samseg for sub-{self.sub}_ses{self.ses}!')
#             else:
#                 print('step2 no mprage')
#                 try:
#                     logging.info(f'Running Samseg for sub-{self.sub} ses-{self.ses}...')
                    
#                     #mri_convert pour avoir les FLAIR et MPRAGE_used en mgz au bon endroit
#                     #convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz'
                    
#                     subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz', shell=True).wait()
                    
#                     # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
#                     # convert = f'mri_convert /usr/local/freesurfer/subjects/sub-{self.sub}_MPRAGE_used.nii.gz /usr/local/freesurfer/subjects/sub-{self.sub}_MPRAGE_used.mgz'
#                     # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/usr/local/freesurfer/subjects'], command=convert)
                 
                    
#                     # https://surfer.nmr.mgh.harvard.edu/fswiki/Samseg
#                     # samseg = f'run_samseg -i /input/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o /media --save-posteriors'
#                     self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = [f'{sub_ses_derivative_path_segment}/SAMSEG_results'])
#                     subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o {sub_ses_derivative_path_segment}/SAMSEG_results --save-posteriors', shell=True).wait()
                   
#                     # subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o {sub_ses_derivative_path_segment} --save-posteriors', shell=True).wait()
                    
#                     # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_transfo}:/input', f'sub_ses_derivative_path_segment:/media'],command=samseg)
#                     #subprocess.Popen(f'docker run --rm -e FS_LICENSE=/data/license.txt -v {license_location}:/data -v {sub_ses_derivative_path_transfo}:/input -v {sub_ses_derivative_path_segment}:/media freesurfer/freesurfer:7.2.0 {samseg}', shell=True).wait()
                    
#                     # convert = f'mri_convert /usr/local/freesurfer/subjects/posteriors/Lesions.mgz /usr/local/freesurfer/subjects/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz'
                    
#                     subprocess.Popen(f'mri_convert {sub_ses_derivative_path_segment}/SAMSEG_result/posteriors/Lesions.mgz {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz', shell=True).wait()
                    
#                     # self.client.containers.run('freesurfer/freesurfer:7.2.0', auto_remove=True, environment =['FS_LICENSE=/data/license.txt'], volumes=[f'{license_location}:/data', f'{sub_ses_derivative_path_segment}:/usr/local/freesurfer/subjects'], command=convert)
              
              
           
        
#                 # Change the name of segmentation output
#                 #shutil.move(pjoin(sub_ses_derivative_path_segment, f'seg.mgz'), pjoin(sub_ses_derivative_path_segment, f'sub{self.sub}_lesions.mgz'))
#                 except Exception as e:
#                     print(f'Error {e} while running Samseg for sub-{self.sub}_ses{self.ses}!')
             
#             #Binarizing the lesion probability  mask     
#             try:
#                 logging.info(f'Binarizing lesion probability mask for sub-{self.sub} ses-{self.ses}...')
               
#                 threshold = 0.5
#                 image = nib.load(f'{sub_ses_derivative_path_segment}/SAMSEG_results/posteriors/Lesions.mgz')
#                 lesions = image.get_fdata()
#                 lesions[lesions >= threshold] = 1
#                 lesions[lesions < threshold] = 0
            
#                 nifti_out = nib.Nifti1Image(lesions, affine=image.affine)
#                 nib.save(nifti_out, f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz')
                
#             except Exception as e:
#                 print(f'Error {e} while binarizing lesion probability mask for sub-{self.sub}_ses{self.ses}!')
                
#         print('end SAMSEG')
               
      
        
#         if self.recon_all:
#             #print("debug: recon-all begin")
#             self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories=directory_fs_sub_ses)
#             subprocess.Popen(f'recon-all -all -i {sub_ses_directory}/{mprage} -subjid sub-{self.sub}_ses-{self.ses}_MPRAGE -sd {sub_ses_fs_path}', shell=True).wait()
        
#         if self.step3 == True:
#             print('step 3')  
            
#             # Prend un des produits de recon-all et le reconvertit en nii.gz pour la suite
#             print(f'step 3.1 : Transform the Freesurfer segmentation (product of recon-all) into the normalized space (Samseg space)')
#             try:
#                 logging.info(f'mri/orig.mgz --> mri/orig.nii.gz and mri/aseg.mgz --> mri.aseg.nii.gz')
                
#                 subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.mgz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz', shell=True).wait()
#                 subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.mgz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz', shell=True).wait()

#             except Exception as e:
#                 print(f'Error {e} while converting mri/orig.mgz --> mri/orig.nii.gz and/or mri/aseg.mgz --> mri.aseg.nii.gz')

                        
#             try:
#                 logging.info(f'Registration Orig on MPRAGE_used')
                
#                 subprocess.Popen(f'$ANTs_registration -d 3 -n 4 -f {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz -m {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -t r -o {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_used', shell=True).wait()

                
#             except Exception as e:
#                 print(f'Error {e} while registrating Orig on MPRAGE_used')
                
            
#             try:
#                 logging.info(f'Registration aseg on MPRAGE_used')
                
#                 #https://manpages.ubuntu.com/manpages/bionic/man1/antsApplyTransforms.1.html
                
#                 subprocess.Popen(f'$ANTSPATH/antsApplyTransforms -d 3 -i {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz -r {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_used.nii.gz -n GenericLabel -t {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_used0GenericAffine.mat -o {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg_used.nii.gz', shell=True).wait()
                
#             except Exception as e:
#                 print(f'Error {e} while registrating aseg on MPRAGE_used')
                
#             print(f'step 3.2 : Transform de binarized lesion mask (product of Samseg) into freesurfer space')
            
            
#             try:
#                 logging.info(f'Transforming the binarized lesion mask (product of Samseg) into freesurfer space')
                
#                 subprocess.Popen(f'$ANTSPATH/antsApplyTransforms -d 3 -i {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz -r {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -n GenericLabel -t [{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_used0GenericAffine.mat, 1] -o {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz', shell=True).wait()
#                 subprocess.Popen(f'$ANTSPATH/antsApplyTransforms -d 3 -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_used.nii.gz -r {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -n GenericLabel -t [{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_used0GenericAffine.mat, 1] -o {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.nii.gz', shell=True).wait()
                
#                 subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.mgz', shell=True).wait()
#                 subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.nii.gz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.mgz', shell=True).wait()

#             except Exception as e:
#                 print(f'Error {e} while transforming the binarized lesion mask (product of Samseg) into freesurfer space')
            
            
#             print(f'step 3.3 : Merge the brain segmentation files with the lesion masks in both samseg and Freesurfer spaces')
            
#             def update_aseg_norm(subject, path):
#                 """
#                 Merge normalized Freesurfer brain segmentation with the lesion segmentation 
#                 performed by samseg. 
#                 Parameters
#                 ----------
#                 subject : TYPE str
#                     Subject id.
#                 Returns
#                 -------
#                 None.
#                 """      
#                 # Load lesion mask
#                 lesion_image = nib.load(f'{path}/sub-{subject}_ses-{self.ses}_lesions_binary.nii.gz')
#                 lesion_mx = lesion_image.get_fdata()
                
#                 lesion_mask = ma.masked_not_equal(lesion_mx,1)

#                 # Load Freesurfer segmentation mask (aseg)
#                 aseg_image = nib.load(f'{path}/sub-{subject}_ses-{self.ses}_aseg_used.nii.gz')
#                 aseg_mx = aseg_image.get_fdata()
                
#                 # Set all voxels of aseg marked as lesion in the lesion mask to 99 (Freesurfer lesion id)
#                 aseg_mask = ma.masked_array(aseg_mx, np.logical_not(lesion_mask.mask), fill_value=99).filled()


#                 # Save resulting matrix to nifti file
#                 nifti_out = nib.Nifti1Image(aseg_mask, affine=aseg_image.affine, header=aseg_image.header)

#                 nifti_out_2 = nib.Nifti1Image(nifti_out, affine=aseg_image.affine, header=aseg_image.header)
#                 nib.save(nifti_out, f'{path}/sub-{subject}_ses-{self.ses}_aseg_lesions.nii.gz')
#                 # nifti_out.to_filename(f'{path}/sub-{subject}_aseg_lesions.nii.gz')
                
#             def update_aseg_fs(subject, path):
                
#                 """
#                 Merge Freesurfer brain segmentation with the lesion segmentation 
#                 performed by samseg in Freesurfer's space.
#                 Parameters
#                 ----------
#                 subject : TYPE str
#                     Subject id.
#                 Returns
#                 -------
#                 None.
#                 """
                
#                 # Load lesion mask
#                 lesion_image = nib.load(f'{path}/sub-{subject}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz')
#                 lesion_mx = lesion_image.get_fdata()
                
#                 lesion_mask = ma.masked_not_equal(lesion_mx,1)
                
#                 # Loa Freesurfer segmentation mask (aseg)
#                 aseg_image = nib.load(f'{path}/sub-{subject}_ses-{self.ses}_MPRAGE/mri/aseg.mgz')
#                 aseg_mx = aseg_image.get_fdata()
                
#                 # Set all voxels of aseg marked as lesion in the lesion ask to 99 (Freesurfer lesion id)
#                 aseg_mask = ma.masked_array(aseg_mx, np.logical_not(lesion_mask.mask), fill_value=99).filled()
                
#                 # Save resulting matrix to nifti file
#                 nifti_out = nib.Nifti1Image(aseg_mask, affine=aseg_image.affine)
#                 nib.save(nifti_out, f'{path}/sub-{subject}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz')

            
            
#             def update_aseg(subject, path_fs, path_norm):
#                 """
#                 Updates aseg in Freesurfer space as well as in Samseg space according to the lesion mask
#                 created by samseg and then binarized.
#                 Parameters
#                 ----------
#                 subject : TYPE str
#                     Subject id.
#                 Returns
#                 -------
#                 None.
#                 """
#                 update_aseg_norm(subject, path_norm)
#                 update_aseg_fs(subject, path_fs)
                
#             # Step 3.3
#             try:
#                 update_aseg(self.sub, sub_ses_fs_path, sub_ses_derivative_path_segment)
#             except Exception as e:
#                 print(e)
            
            
#             print(f'step 3.4 : Lesion labelling, volumetry and location')
            
#             WHITE_MATTER   = 2
#             GRAY_MATTER    = 3
#             VENTRICLES     = 4
#             INFRATENTORIAL = 16 
            
#             def load_segmentations(subject):
#                 """
#                 Loads the segmentation image and matrix as well as the lesion matrix
#                 Parameters
#                 ----------
#                 subject : TYPE <str>
#                     Subject id.
#                 Returns
#                 -------
#                 aseg_image : TYPE <nibabel.freesurfer.mghformat.MGHImage>
#                     Image of the Freesurfer segmentation mask.
#                 seg:         TYPE 3D numpy.ndarray
#                     Matrix of segmentations.
#                 lesion:      TYPE 3D numpy.ndarray
#                     Lesion matrix.
#                 """
#                 # Load segmentations
#                 aseg_img = nib.load(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg_lesions.nii.gz')
#                 seg = aseg_img.get_fdata()
                
#                 # Make lesion matrix from segmentations matrix
#                 lesion = seg.copy()
#                 lesion[lesion!=99] = 0
#                 lesion[lesion==99] = 1
                
#                 return aseg_img, seg, lesion
            
            
            
            
            
#             def make_lesions_csv(subject, minimum_lesion_size=5):
#                 """
#                 Makes the lesion based database (lesions.csv) that regroups informations about
#                 the lesions of one subject (label - volume - location). 
#                 Parameters
#                 ----------
#                 subject : TYPE <str>
#                     Subject id.
#                 minimum_lesion_size : TYPE <int>, optional
#                     Minimum size for a lesion to be considered as such. The default is 5.
#                 Returns
#                 -------
#                 None.
#                 """
#                 # Load segmentations
#                 image, aseg, lesion = load_segmentations(subject) 
                
#                 # Get number of components (thus number of lesions)
#                 structure = np.ones((3, 3, 3))
#                 labeled_lesions, nlesions = label(lesion,structure)
                
#                 print("Number of lesions before discarding: {0}".format(nlesions))
                
#                 id_lesions_dic = {}
                            
#                 # For every lesion
#                 for lesion_id in range(1,nlesions+1):
#                     # Create lesion mask for this specific lesion
#                     lesions_mskd = ma.masked_where(labeled_lesions != lesion_id, labeled_lesions)
                    
#                     # Compute the lesion volume
#                     lesion_voxel_volume_count = lesions_mskd.sum() // lesion_id
                    
                    
#                     if lesion_voxel_volume_count > minimum_lesion_size:
#                         print("\n\nLesion {0}: {1} voxels".format(lesion_id, lesion_voxel_volume_count))
                        
#                         # Get the lesion location
#                         loc_20,_,_ = lesion_location(subject, lesion_id, lesion_mx=labeled_lesions,
#                                                    aseg_mx=aseg, percentage=0.2)
#                         # loc_30,_,_ = lesion_location(subject, lesion_id, lesion_mx=labeled_lesions,
#                         #                            aseg_mx=aseg, percentage=0.3)
                        
#                         id_lesions_dic[lesion_id] = [lesion_voxel_volume_count, loc_20] #, loc_30]#, loc_40, loc_50]
                        
#                     else: 
#                         # Discard lesion if size is inferior to the minimum lesion size
#                         print("\n\nLesion {0}: {1} voxels ==> Discarded (too small)".format(lesion_id, lesion_voxel_volume_count))
#                         #labeled_lesions[labeled_lesions == lesion_id] = 0 # Leave commented, not working
                
#                 print('DEBUG: make_lesions_csv: end for loop')
                
#                 self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories=[pjoin(self.bids.root_dir, 'derivatives', derivative, samseg, 'stats'), pjoin(self.bids.root_dir, 'derivatives', derivative, samseg, 'stats', f'sub-{self.sub}'), f'{sub_ses_derivative_path_stats}'])
                
#                 # Make the database
#                 columns = ["Voxel Volume", "Location"] #" 20%", "Location 30%"]
                
#                 df = pd.DataFrame.from_dict(id_lesions_dic, orient='index', columns=columns)
#                 df.to_csv(f'{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}_lesions.csv')
                
#                 # Save the lesion mask with labels to a nifti file
#                 nifti_out = nib.Nifti1Image(labeled_lesions, affine=image.affine)
#                 nib.save(nifti_out, f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_labeled_lesions.nii.gz')
                
                
                
                
                
#             def lesion_location(subject, lesion_label, lesion_mx=None, aseg_mx=None, percentage=0.2):
#                 """
#                 Finds the location of a lesion
#                 Parameters
#                 ----------
#                 subject : TYPE <str>
#                     Subject id.
#                 lesion_label : TYPE <int>
#                     Label id for the lesion of interest.
#                 lesion_mx : TYPE 3D numpy.ndarray, optional
#                     Matrix of labeled lesions. The default is retrieved based on the machine and subject path.
#                 aseg_mx : TYPE 3D numpy.ndarray, optional
#                     Matrix of labeled brain structures. The default is retrieved based on the machine and subject path.
#                 percentage : TYPE <int>, optional
#                     Percentage of the lesion volume that has to match with the dilated brain structure. The default is 0.2.
#                 Returns
#                 -------
#                 TYPE <str>
#                     Lesion location. Either "White Matter", "Cortical or juxta-cortical", "Periventricular" or "Infratentorial".
#                 lesion_volume : TYPE <int>
#                     Lesion volume (voxel count).
#                 """
                
#                 if lesion_mx is None:
#                     # Load lesion mask
#                     lesion_image = nib.load(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_labeled_lesions.nii.gz')
#                     lesion_mx = lesion_image.get_fdata()
                    
#                 if aseg_mx is None:
#                     # Load segmentation
#                     aseg_image = nib.load(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg.mgz')
#                     aseg_mx = aseg_image.get_fdata()
                
                
#                 # Regroup left and right structures into the same label 
#                 aseg_mx[aseg_mx == 41] = WHITE_MATTER #White matter
#                 aseg_mx[aseg_mx == 42] = GRAY_MATTER #Gray matter
#                 aseg_mx[aseg_mx == 43] = VENTRICLES #Ventricle
#                 aseg_mx[aseg_mx == 7]  = INFRATENTORIAL #Left Cerebellum Cortex -> Brainstem
#                 aseg_mx[aseg_mx == 8]  = INFRATENTORIAL #Left Cerebellum WM -> Brainstem
#                 aseg_mx[aseg_mx == 47] = INFRATENTORIAL #Right Cerebellum Cortex -> Brainstem
#                 aseg_mx[aseg_mx == 46] = INFRATENTORIAL #Right Cerebellum WM -> Brainstem
                
#                 results = []
#                 dic = {WHITE_MATTER: "white matter", GRAY_MATTER: "gray matter", 
#                        VENTRICLES: "ventricles", INFRATENTORIAL: "infratentorial structures"}
                
#                 for seg,iterations in [(GRAY_MATTER, 1), (VENTRICLES, 3), (INFRATENTORIAL, 1)]:
                    
#                     print("Dilating " + dic[seg] + "...", end= " ")
                    
#                     # Make the brain structure segmentation mask (other segmentations removed)
#                     aseg_mask = ma.masked_not_equal(aseg_mx, seg)
#                     aseg_mask.fill_value = 0
#                     aseg_mask = aseg_mask.filled()
                    
#                     # Dilate the brain structure 'iterations' timesaseg_temp 
#                     aseg_temp = binary_dilation(aseg_mask, iterations=iterations).astype(aseg_mx.dtype) # Binary mask
                    
#                     # Append the results
#                     matching_voxels = count_matching_lesion_voxels(lesion_mx, aseg_temp, lesion_label, seg)
#                     print( str(matching_voxels) + " voxels in common with the lesion")
#                     results.append(matching_voxels)
                
#                 # Get the lesion volume
#                 lesions_mskd = ma.masked_where(lesion_mx != lesion_label, lesion_mx)
#                 lesion_volume = lesions_mskd.sum() // lesion_label
                
#                 index = {-1:"White Matter", 0:"Cortical or juxta-cortical", 1:"Periventricular", 2: "Infratentorial"}
                
#                 # Set the lesion location as white matter if the count of overlapping voxels do not 
#                 # exceed the percentage of the lesion volume
#                 loc = results.index(max(results))
#                 if (loc == 0 or loc == 1) and max(results) < percentage*lesion_volume:
#                     loc = -1
                
#                 return index[loc], lesion_volume, results
                 
            
#             def count_matching_lesion_voxels(lesion_mx, segmentation_mx, lesion, segmentation):
#                 """
#                 Counts the number of voxels where 
#                     lesion_mx[index]       = lesion         and 
#                     segmentation_mx[index] = segmentation 
#                 for the same index
#                 Parameters
#                 ----------
#                 lesion_mx : 3D numpy.ndarray
#                     Matrix of labeled lesions.
#                 segmentation_mx : 3D numpy.ndarray
#                     Matrix of labeled brain segmentation.
#                 lesion : TYPE <int>
#                     Label for the lesion of interest.
#                 segmentation : TYPE <int>
#                     Label for the brain structure of interest.
#                 Returns
#                 -------
#                 TYPE <int>
#                     Count of matching voxels.
#                 """
                
                
#                 les_mx = lesion_mx.copy()
                
#                 # Set all voxels whose value differ from the lesion id to -1
#                 les_mx = ma.masked_not_equal(les_mx, lesion)
#                 les_mx.fill_value = -1
#                 les_mx = les_mx.filled()
                
#                 # Set all voxels whose value equal to the lesion id to 1
#                 les_mx[les_mx == lesion] = 1
                
#                 return np.sum(les_mx == segmentation_mx)   
                
                
                
                
                
#             def make_location_mask(subject, percentage=20):
#                 """
#                 Makes a lesion location mask based on the lesion based db (lesions.csv)
#                 Parameters
#                 ----------
#                 subject : TYPE <str>
#                     Subject id.
#                 percentage : TYPE <int>, optional
#                     Percentage of the lesion volume that has to match with the dilated brain 
#                     structure. The default is 20.
#                 Returns
#                 -------
#                 None.
#                 """
#                 # Retrieve lesion based database
#                 df = pd.read_csv(f'{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}_lesions.csv')
#                 locations = list(df["Location"]) # {0}%".format(percentage)])
#                 ids = list(df["Unnamed: 0"])
                
#                 lesion_image = nib.load(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_labeled_lesions.nii.gz')
#                 lesion_mx = lesion_image.get_fdata()
                
#                 lesion_loc = lesion_mx.copy()
                
#                 dictionary = {"White Matter":100, "Cortical or juxta-cortical":200, "Periventricular":300, "Infratentorial":400}
                
#                 for i in range(len(locations)):
#                     lesion_loc[lesion_loc == ids[i]] = dictionary[locations[i]]
                
#                 nifti_out = nib.Nifti1Image(lesion_loc,affine=lesion_image.affine)
#                 nib.save(nifti_out, f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesion_locations.nii.gz')
            
                
                
                
                
#             # Step 3.4 
#             make_lesions_csv(self.sub)
#             print('make_location_mask')
#             make_location_mask(self.sub, 20)
            
            
#             print('Step 3.5 : Recompute Freesurfer volumetry based on the new segmentation file')
            
            
#             try:
#                 logging.info(f'Converting mri/aseg_lesions.nii.gz --> mri/aseg_lesion.mgz to use it in freesurfer ')
                
#                 subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz', shell=True).wait()
#                 shutil.copy(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz', f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg_lesions.nii.gz')

#             except Exception as e:
#                 print(f'Error {e} while converting mri/aseg_lesions.nii.gz --> mri/aseg_lesion.mgz')
                
#             try:
#               logging.info(f'Executing mri_segstats on aseg_lesion.mgz')
              
#               subprocess.Popen(f'mri_segstats --seed 1234 --seg {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz \
#                                --sum {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats --pv {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz \
#                                  --empty --brainmask {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/brainmask.mgz --brain-vol-from-seg --excludeid 0 \
#                                    --excl-ctxgmwm --supratent --subcortgray --in {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz \
#                                      --in-intensity-name norm --in-intensity-units MR --etiv --surf-wm-vol --surf-ctx-vol \
#                                        --totalgray --euler --ctab \
#                                          /home/stluc/Programmes/freesurfer/ASegStatsLUT.txt --sd {sub_ses_fs_path} --subject sub-{self.sub}_ses-{self.ses}_MPRAGE', shell=True).wait()

#             except Exception as e:
#               print(f'Error {e} while Executing mri_segstats on aseg_lesion.mgz')
              
#             print(f'Step 3.6 : Make subject-{self.sub}_ses-{self.ses}.csv')            
            
#             def get_brain_volumes(subject):
#                 """
#                 Retrieves brain volumes from the aseg_lesions.stats file produced by volumetry.sh
#                 Parameters
#                 ----------
#                 subject : TYPE <str>
#                     Subject id.
#                 Returns
#                 -------
#                 stats : TYPE <dict>
#                     Dictionary of brain volumes.
#                 """
#                 stats={}
                
#                 with open(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats') as file:
#                     for line in file:
#                         if "Estimated Total Intracranial Volume," in line:
#                             lst = line.split(', ')
#                             stats['Intracranial volume'] = float(lst[3])
#                         elif "Brain Segmentation Volume," in line:
#                             lst = line.split(', ')
#                             stats['Brain volume'] = float(lst[3])
#                         elif "Volume of ventricles and choroid plexus," in line:
#                             lst = line.split(', ')
#                             stats['Ventricles'] = float(lst[3])
#                         elif "Total gray matter volume," in line:
#                             lst = line.split(', ')
#                             stats['Gray matter'] = float(lst[3])
#                         elif "Total cerebral white matter volume," in line:
#                             lst = line.split(', ')
#                             stats['White matter'] = float(lst[3])
#                         elif "Left-Caudate" in line:
#                             lst = line.split(' ')
#                             column = 0
#                             for el in lst:
#                                 if el != '':
#                                     if column == 5:
#                                         left_caudate = float(el)
#                                     column+=1
#                         elif "Right-Caudate" in line:
#                             lst = line.split(' ')
#                             column = 0
#                             for el in lst:
#                                 if el != '':
#                                     if column == 5:
#                                         right_caudate = float(el)
#                                     column+=1
#                         elif "Left-Putamen" in line:
#                             lst = line.split(' ')
#                             column = 0
#                             for el in lst:
#                                 if el != '':
#                                     if column == 5:
#                                         left_putamen = float(el)
#                                     column+=1
#                         elif "Right-Putamen" in line:
#                             lst = line.split(' ')
#                             column = 0
#                             for el in lst:
#                                 if el != '':
#                                     if column == 5:
#                                         right_putamen = float(el)
#                                     column+=1
#                         elif "Left-Thalamus" in line:
#                             lst = line.split(' ')
#                             column = 0
#                             for el in lst:
#                                 if el != '':
#                                     if column == 5:
#                                         left_thalamus = float(el)
#                                     column+=1
#                         elif "Right-Thalamus" in line:
#                             lst = line.split(' ')
#                             column = 0
#                             for el in lst:
#                                 if el != '':
#                                     if column == 5:
#                                         right_thalamus = float(el)
#                                     column+=1
#                         elif " WM-hypointensities" in line:
#                             lst = line.split(' ')
#                             column = 0
#                             for el in lst:
#                                 if el != '':
#                                     if column == 5:
#                                         wm_hypo = float(el)
#                                     column+=1
                    
#                     stats['Caudate']=left_caudate+right_caudate
#                     stats['Putamen']=left_putamen+right_putamen
#                     stats['Thalamus']=left_thalamus+right_thalamus
#                     stats['WM-hypointenisities'] = wm_hypo
                    
#                     brainvol = stats["Intracranial volume"]
#                     for key,value in stats.items():
#                         if key != "Intracranial volume":
#                             stats[key] = value/brainvol
                   
                    
#                     return stats
                
                
#             def get_lesions_information(subject, stats):
#                 """
#                 Updates stats with the subjects' lesion informations
#                 Parameters
#                 ----------
#                 subject : TYPE <str>
#                     Subject id.
#                 stats : TYPE <dict>
#                     Dictionary of brain volumes.
#                 Returns
#                 -------
#                 stats : TYPE <dict>
#                     Dictionary of brain volumes and lesion informations.
#                 wm_lesions: TYPE <int>
#                     Total volume of white matter lesions
#                 """
                
#                 df = pd.read_csv(f'{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}_lesions.csv')
                
#                 lesion_count  = df['Unnamed: 0'].count()
#                 lesion_volume = df['Voxel Volume'].sum()
                
#                 stats["Number of lesions"]   = lesion_count
#                 stats["Total lesion volume"] = lesion_volume
                
#                 wm_lesions = df[df['Location'] != 'Infratentorial']['Voxel Volume'].sum()
                
#                 wml = df[df["Location"] == 'White Matter']['Voxel Volume'].sum()
#                 peril = df[df["Location"] == 'Periventricular']['Voxel Volume'].sum()
#                 gml = df[df["Location"] == 'Cortical or juxta-cortical']['Voxel Volume'].sum()
#                 infratl = df[df["Location"] == 'Infratentorial']['Voxel Volume'].sum()
                
#                 stats['White matter lesions %'] = (wml / lesion_volume)*100
#                 stats['Cortical or juxta-cortical lesions %'] = (gml / lesion_volume)*100
#                 stats['Periventricular lesions %'] = (peril / lesion_volume)*100
#                 stats['Infratentorial lesions %'] = (infratl / lesion_volume)*100
                
                
                
#                 return stats, wm_lesions
                
                
            
#             def make_subject_csv(subject):
                
#                 stats = get_brain_volumes(subject)
#                 stats, wm_lesions = get_lesions_information(subject,stats)
                
#                 ic_volume = stats['Intracranial volume']
                
#                 stats['White matter'] = stats['White matter'] + stats['WM-hypointenisities'] 
#                 stats['Total lesion volume'] = stats['Total lesion volume'] / ic_volume 
                
#                 df = pd.DataFrame.from_dict(stats, orient='index', columns = [subject])
#                 df = df.transpose()
#                 df.to_csv(f'{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}.csv')
                
#             # Step 3.6 
#             make_subject_csv(self.sub)
                    
            
#         self.finished.emit()
            
            
            
            
            
            
            
            