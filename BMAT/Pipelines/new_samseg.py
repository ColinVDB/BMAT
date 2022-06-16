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

        self.setWindowTitle("(new_samseg) LesVolLoc")
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
        self.action = LesVolLocSegWorker(self.bids, self.subjects_and_sessions, normalization=self.normalization, mprage=self.mprage, step1=self.step1, step2=self.step2, recon_all=self.recon_all, step3=self.step3)
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

    def __init__(self, bids, subjects_and_sessions, normalization=False, mprage=False, step1=False, step2=False, recon_all=False, step3=False):
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
        self.pipeline = "LesVolLoc"
        self.freesurfer_license = '/home/stluc/Programmes/BMAT/BMAT/license.txt'
        
        
    def run(self):
        for sub, sess in self.subjects_and_sessions:
            for ses in sess:
                self.sub = sub
                self.ses = ses
                print(f'Running LesVolLoc for sub-{sub} ses-{ses}')
                # self.run_LesVolLoc()
                
                # Define paths and filenames for a certain SUBJECT and SESSION
                fs = 'FreeSurfer'
                derivative = 'LesVolLoc'
                samseg = 'SAMSEG'
                segment = 'segmentation'
                transfo = 'transformation'
                sub_ses_directory = pjoin(self.bids.root_dir, f'sub-{self.sub}', f'ses-{self.ses}', 'anat')
                flair = f'sub-{self.sub}_ses-{self.ses}_FLAIR.nii.gz'
                mprage = f'sub-{self.sub}_ses-{self.ses}_acq-MPRAGE_T1w.nii.gz'
                sub_ses_derivative_path_segment = pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, segment)
                sub_ses_derivative_path_transfo = pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, transfo)
                sub_ses_derivative_path_stats = pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, 'stats')
                sub_ses_fs_path = pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', fs)
                
                # Define list of directories to create
                directorysegment = [pjoin('derivatives', derivative), pjoin('derivatives', derivative, f'sub-{self.sub}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, segment)]
                directorytransfo = [pjoin('derivatives', derivative), pjoin('derivatives', derivative, f'sub-{self.sub}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, transfo)]
                directorystats = [pjoin('derivatives', derivative), pjoin('derivatives', derivative, f'sub-{self.sub}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, 'stats')]
                directory_fs_sub_ses = [pjoin('derivatives', derivative), pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}'), pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}'), pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', fs)]
                
                # Perform Lesion Segmentation, Localisation and Volumetry
                
                ## Step1 : Preprocessing (normalization and registration FLAIR and MPRAGE)
                if self.step1 == True: 
                    
                    print('Start Preprocessing...')
                    
                    # Pre check
                    ## Create corresponding directory if necessary
                    self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = directorytransfo)
                    
                    # Actions
                    ## Normalization if need 
                    if self.normalization == True:
                        
                        print('normalization')
                        
                        # Pre check
                        ## check if preprocessing has already been done previously, and delete the results if necessary
                        if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed')):
                            shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed'))
                        if pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz')):
                            os.remove(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz'))
                            
                        ## check if files exist
                        if not pexists(pjoin(sub_ses_directory, flair)):
                            print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, flair)}" not Found !')
                            return
                        
                        # Actions
                        ## Normalized FLAIR
                        try:
                            print(f'Resizing FLAIR for sub-{self.sub} ses-{self.ses}...')
                            
                            # subprocess.Popen(f'recon-all -motioncor -i {sub_ses_directory}/{flair} -subjid sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed -sd {sub_ses_derivative_path_transfo}', shell=True).wait()
                            subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_directory}:/media/sub_ses_directory -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && recon-all -motioncor -i /media/sub_ses_directory/{flair} -subjid sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed -sd /media/sub_ses_derivative_path_transfo"', shell=True).wait()
                            
                        except Exception as e:
                            print(f'[ERROR] - {self.pipeline} | {e} when resizing FLAIR for sub-{self.sub}_ses-{self.ses}!')
                            return
                        
                        ## Convert mgz file from freesurfer to nii file 
                        try:
                            print(f'Converting FLAIR_used.mgz to .nii.gz for sub-{self.sub} ses-{self.ses}...')
                            
                            # subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed/mri/orig.mgz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz', shell=True).wait()
                            subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed/mri/orig.mgz /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz"', shell=True).wait()           
                            
                        except Exception as e:
                            print(f'[ERROR] - {self.pipeline} | {e} when converting FLAIR_used.mgz to .nii.gz for sub-{self.sub}_ses{self.ses}!')
                            return
                        
                    ## No normalization
                    else: 
                    
                        print('No Normalization !')
                        
                        # Pre check
                        ## check if preprocessing has already been done previously, and delete the results if necessary
                        if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed')):
                            shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed'))
                        if pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz')):
                            os.remove(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz'))
                            
                        ## check if files exist
                        if not pexists(pjoin(sub_ses_directory, flair)):
                            print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, flair)}" not Found !')
                            return
                        
                        # Actions
                        ## Copy FLAIR in directory of transformations for access simplicity
                        shutil.copyfile(pjoin(sub_ses_directory, flair), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz'))
                    
                    ## Register MPRAGE on FLAIR
                    if self.mprage == True:
                        
                        print('Preprocessing mprage...')
                        
                        # Pre check
                        ## check if files exist
                        if not pexists(pjoin(sub_ses_directory, flair)):
                            print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, flair)}" not Found !')
                            return
                        
                        if not pexists(pjoin(sub_ses_directory, mprage)):
                            print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, mprage)}" not Found !')
                            return
                        
                        
                        # Actions
                        ## Resgistering MPRAGE on FLAIR
                        try:
                            print(f'Registration of MPRAGE on FLAIR_preprocessed for sub-{self.sub} ses-{self.ses}...')
                                                 
                            # subprocess.Popen(f'$ANTs_registration -d 3 -n 4 -f {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz -m {sub_ses_directory}/{mprage} -t r -o {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed', shell=True).wait()
                            subprocess.Popen(f'docker run --rm --privileged -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_directory}:/media/sub_ses_directory colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && \$ANTs_registration -d 3 -n 4 -f /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz -m /media/sub_ses_directory/{mprage} -t r -o /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed"', shell=True).wait()           
                            
                            # Change the name of registration output
                            shutil.move(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessedWarped.nii.gz'), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz'))
                        
                        except Exception as e:
                            print(f'[ERROR] - {self.pipeline} | {e} during registration of MPRAGE on FLAIR_used for sub-{self.sub}_ses{self.ses}!')
                            return
                        
                    else:
                        pass
                    
                    print('End Preprocessing!')
                       
                else:
                    pass
                
                
                ## Step2 : Segmentation using SAMSEG to compute lesion probability mask
                if self.step2 == True:
                    
                    print('Start Segmentating lesions with SAMSEG...')
                    
                    # Pre check
                    ## Create segmentation directories
                    self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = directorysegment)     
                    self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = [f'{sub_ses_derivative_path_segment}/SAMSEG_results'])
                    
                    # Actions
                    ## Run SAMSEG with FLAIR and MPRAGE
                    if self.mprage == True:
                        
                        print('Segmenting with FLAIR & mprage')
                        
                        # Pre check
                        ## check if files exist
                        if not pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz')):
                            file = pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz')
                            print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{file}" not Found !')
                            return
                        
                        if not pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz')):
                            file = pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz')
                            print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{file}" not Found !')
                            return
                        
                        # Actions
                        try:
                            print(f'Running Samseg for sub-{self.sub} ses-{self.ses}...')
                            
                            # subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz', shell=True).wait()
                            subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz"', shell=True).wait()
                            
                            # subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.mgz', shell=True).wait()
                            subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.mgz"', shell=True).wait()
                            
                            # subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.mgz -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz --lesion --lesion-mask-pattern 0 1 --threads 4 -o {sub_ses_derivative_path_segment}/SAMSEG_results --save-posteriors', shell=True).wait()
                            subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && run_samseg -i /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.mgz -i /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz --lesion --lesion-mask-pattern 0 1 --threads 4 -o /media/sub_ses_derivative_path_segment/SAMSEG_results --save-posteriors"', shell=True).wait()
                            
                            # subprocess.Popen(f'mri_convert {sub_ses_derivative_path_segment}/SAMSEG_results/posteriors/Lesions.mgz {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz', shell=True).wait()
                            subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_segment/SAMSEG_results/posteriors/Lesions.mgz /media/sub_ses_derivative_path_segment/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz"', shell=True).wait()
                            
                        except Exception as e:
                            print(f'[ERROR] - {self.pipeline} | {e} while running Samseg for sub-{self.sub}_ses{self.ses}!')
                            return
                        
                    ## Run SAMSEG with only FLAIR 
                    else:
                        
                        print('Segmenting with only FLAIR')
                        
                        # Pre check
                        ## check if files exist
                        if not pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz')):
                            file = pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz')
                            print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{file}" not Found !')
                            return
                        
                        # Actions
                        try:
                            print(f'Running Samseg for sub-{self.sub} ses-{self.ses}...')

                            # subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz', shell=True).wait()
                            subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz"', shell=True).wait()
                            
                            # subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o {sub_ses_derivative_path_segment}/SAMSEG_results --save-posteriors', shell=True).wait()
                            subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && run_samseg -i /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o /media/sub_ses_derivative_path_segment/SAMSEG_results --save-posteriors"', shell=True).wait()
                            
                            # subprocess.Popen(f'mri_convert {sub_ses_derivative_path_segment}/SAMSEG_result/posteriors/Lesions.mgz {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz', shell=True).wait()
                            subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_segment/SAMSEG_result/posteriors/Lesions.mgz /media/sub_ses_derivative_path_segment/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz"', shell=True).wait()
                            
                        except Exception as e:   
                            print(f'[ERROR] - {self.pipeline} | {e} while running Samseg for sub-{self.sub}_ses{self.ses}!')
                            return
                        
                    ## Binarizing the lesion probability  mask    
                    # Pre check
                    ## check if files exist
                    if not pexists(pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_lesions.nii.gz')):
                        file = pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_lesions.nii.gz')
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{file}" not Found !')
                        return
                    
                    try:                
                        # Actions
                        print(f'Binarizing lesion probability mask for sub-{self.sub} ses-{self.ses}...')
                       
                        threshold = 0.5
                        image = nib.load(pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_lesions.nii.gz'))
                        lesions = image.get_fdata()
                        lesions[lesions >= threshold] = 1
                        lesions[lesions < threshold] = 0
                    
                        lesions_nifti = nib.Nifti1Image(lesions, affine=image.affine)
                        # nib.save(lesions_nifti, pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz'))
                        
                    except Exception as e:
                        print(f'[ERROR] - {self.pipeline} | {e} while binarizing lesion probability mask for sub-{self.sub}_ses{self.ses}!')
                        return
                    
                    print('End SAMSEG!')
                           
                ## Run recon-all for volumetry
                if self.recon_all:
                    
                    print('Start computing volumetry with recon-all...')
                    
                    # Pre check
                    ## Create FreeSurfer directory
                    self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories=directory_fs_sub_ses)
                    
                    ## check if files exist
                    if not pexists(pjoin(sub_ses_directory, mprage)):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, flair)}" not Found !')
                        return
                    
                    # Actions
                    try: 
                        # subprocess.Popen(f'recon-all -all -i {sub_ses_directory}/{mprage} -subjid sub-{self.sub}_ses-{self.ses}_MPRAGE -sd {sub_ses_fs_path}', shell=True).wait()
                        subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_directory}:/media/sub_ses_directory -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && recon-all -all -i /media/sub_ses_directory/{mprage} -subjid sub-{self.sub}_ses-{self.ses}_MPRAGE -sd /media/sub_ses_fs_path"', shell=True).wait()
                        
                    except Exception as e:
                        print(f'[ERROR] - {self.pipeline} | {e} while computing volumetry with recon-all for sub-{self.sub}_ses{self.ses}!')
                        return
                    
                    print('End recon-all!')
                
                ## Merge SAMSEG and FreeSurfer Results for lesion volumetry and localization
                if self.step3 == True:
                    
                    print('Start Localizing and computing volumetry of the lesions...')  
                    
                    # Pre Check
                    ## Create stats directory
                    self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories=directorystats)
                    
                    # Actions
                    ## Transform the Freesurfer segmentation (product of recon-all) into the normalized space (Samseg space)
                
                    print(f'step 3.1 : Transform the Freesurfer segmentation (product of recon-all) into the normalized space (Samseg space)')
                    
                    # Pre check
                    ## check if files exist
                    if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.mgz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.mgz" not Found !')
                        return
                    
                    if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.mgz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.mgz" not Found !')
                        return
                    
                    if not pexists(f'{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz" not Found !')
                        return       
                    
                    # Actions 
                    ## convert orig/aseg.mgz -> nii.gz            
                    try:
                        print(f'mri/orig.mgz --> mri/orig.nii.gz and mri/aseg.mgz --> mri.aseg.nii.gz')
                        
                        # subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.mgz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz', shell=True).wait()
                        subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.mgz /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz"', shell=True).wait()
                        
                        # subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.mgz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz', shell=True).wait()
                        subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.mgz /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz"', shell=True).wait()

                    except Exception as e:
                        print(f'[ERROR] - {self.pipeline} | {e} while converting mri/orig.mgz --> mri/orig.nii.gz and/or mri/aseg.mgz --> mri.aseg.nii.gz')
                        return
                    
                    ## Registration of orig to MPRAGE_preprocessed            
                    try:
                        print(f'Registration Orig on MPRAGE_preprocessed')
                        
                        # subprocess.Popen(f'$ANTs_registration -d 3 -n 4 -f {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz -m {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -t r -o {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed', shell=True).wait()
                        subprocess.Popen(f'docker run --rm --privileged -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && \$ANTs_registration -d 3 -n 4 -f /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz -m /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -t r -o /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed"', shell=True).wait()

                    except Exception as e:
                        print(f'[ERROR] - {self.pipeline} | {e} while registrating Orig on MPRAGE_preprocessed')
                        return
                    
                    ## Registration of aseg to MPRAGE_preprocessed
                    try:
                        print(f'Registration aseg on MPRAGE_preprocessed')
                        
                        # subprocess.Popen(f'$ANTSPATH/antsApplyTransforms -d 3 -i {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz -r {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz -n GenericLabel -t {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat -o {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg.nii.gz', shell=True).wait()
                        subprocess.Popen(f'docker run --rm --privileged -v {sub_ses_fs_path}:/media/sub_ses_fs_path -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && \$ANTs_applyTransforms -d 3 -i /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz -r /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz -n GenericLabel -t /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat -o /media/sub_ses_derivative_path_segment/sub-{self.sub}_ses-{self.ses}_aseg.nii.gz"', shell=True).wait()
                        
                    except Exception as e:
                        print(f'[ERROR] - {self.pipeline} | {e} while registrating aseg on MPRAGE_used')
                        return
                    
                    print(f'step 3.2 : Transform de binarized lesion mask (product of Samseg) into freesurfer space')
                    
                    # Pre check
                    ## check if files exist
                    if not pexists(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz" not Found !')
                        return    
                    
                    if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz" not Found !')
                        return     
                    
                    if not pexists(f'{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat" not Found !')
                        return 
                    
                    if not pexists(f'{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz" not Found !')
                        return    
                    
                    # Actions
                    ## Transforming the binarized lesion mask (product of Samseg) into freesurfer space
                    try:
                        logging.info(f'Transforming the binarized lesion mask (product of Samseg) into freesurfer space')
                        
                        # subprocess.Popen(f'$ANTSPATH/antsApplyTransforms -d 3 -i {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz -r {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -n GenericLabel -t [{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat, 1] -o {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz', shell=True).wait()
                        subprocess.Popen(f'docker run --rm --privileged -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment -v {sub_ses_fs_path}:/media/sub_ses_fs_path -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && \$ANTs_applyTransforms -d 3 -i /media/sub_ses_derivative_path_segment/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz -r /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -n GenericLabel -t [/media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat, 1] -o /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz"', shell=True).wait()
                        
                        # subprocess.Popen(f'$ANTSPATH/antsApplyTransforms -d 3 -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz -r {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -n GenericLabel -t [{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat, 1] -o {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.nii.gz', shell=True).wait()
                        subprocess.Popen(f'docker run --rm --privileged -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && \$ANTs_applyTransforms -d 3 -i /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz -r /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -n GenericLabel -t [/media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat, 1] -o /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.nii.gz"', shell=True).wait()
                        
                        # subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.mgz', shell=True).wait()
                        subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.mgz"', shell=True).wait()
                        
                        # subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.nii.gz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.mgz', shell=True).wait()
                        subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.nii.gz /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.mgz"', shell=True).wait()

                    except Exception as e:
                        print(f'[ERROR] - {self.pipeline} | {e} while transforming the binarized lesion mask (product of Samseg) into freesurfer space')
                        return
                    
                    print(f'step 3.3 : Merge the brain segmentation files with the lesion masks in both samseg and Freesurfer spaces')
                    
                    # Pre check
                    
                    # Actions            
                    def update_aseg_norm(subject, session, path):
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
                        lesion_image = nib.load(f'{path}/sub-{subject}_ses-{session}_lesions_binary.nii.gz')
                        lesion_mx = lesion_image.get_fdata()
                        
                        lesion_mask = ma.masked_not_equal(lesion_mx,1)

                        # Load Freesurfer segmentation mask (aseg)
                        aseg_image = nib.load(f'{path}/sub-{subject}_ses-{session}_aseg.nii.gz')
                        aseg_mx = aseg_image.get_fdata()
                        
                        # Set all voxels of aseg marked as lesion in the lesion mask to 99 (Freesurfer lesion id)
                        aseg_mask = ma.masked_array(aseg_mx, np.logical_not(lesion_mask.mask), fill_value=99).filled()

                        # Save resulting matrix to nifti file
                        aseg_norm_nifti = nib.Nifti1Image(aseg_mask, affine=aseg_image.affine)

                        # nib.save(aseg_norm_nifti, f'{path}/sub-{subject}_ses-{session}_aseg_lesions.nii.gz')


                        
                    def update_aseg_fs(subject, session, path):
                        
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
                        lesion_image = nib.load(f'{path}/sub-{subject}_ses-{session}_MPRAGE/mri/lesions_fs.nii.gz')
                        lesion_mx = lesion_image.get_fdata()
                        
                        lesion_mask = ma.masked_not_equal(lesion_mx,1)
                        
                        # Loa Freesurfer segmentation mask (aseg)
                        aseg_image = nib.load(f'{path}/sub-{subject}_ses-{session}_MPRAGE/mri/aseg.nii.gz')
                        aseg_mx = aseg_image.get_fdata()
                        
                        # Set all voxels of aseg marked as lesion in the lesion ask to 99 (Freesurfer lesion id)
                        aseg_mask = ma.masked_array(aseg_mx, np.logical_not(lesion_mask.mask), fill_value=99).filled()
                        
                        # Save resulting matrix to nifti file
                        aseg_fs_nifti = nib.Nifti1Image(aseg_mask, affine=aseg_image.affine)
                        # nib.save(aseg_fs_nifti, f'{path}/sub-{subject}_ses-{session}_MPRAGE/mri/aseg_lesions.nii.gz')

                    
                    
                    def update_aseg(subject, session, path_fs, path_norm):
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
                        update_aseg_norm(subject, session, path_norm)
                        update_aseg_fs(subject, session, path_fs)
                        
                    # Step 3.3: Merge the brain segmentation files with the lesion masks in both samseg and Freesurfer spaces
                    
                    # Pre check
                    ## check if files exist
                    if not pexists(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz" not Found !')
                        return 
                    
                    if not pexists(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg.nii.gz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg.nii.gz" not Found !')
                        return 
                    
                    if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz" not Found !')
                        return 
                    
                    if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz" not Found !')
                        return 
                    
                    # Actions
                    try:
                        update_aseg(self.sub, self.ses, sub_ses_fs_path, sub_ses_derivative_path_segment)
                    except Exception as e:
                        print(f'[ERROR] - {self.pipeline} | {e} while merging brain segmentation files sith the lesion masks in both samseg and freesurfer space')
                    
                    # Setp 3.4: Lesion labelling, volumetry and location
                    print(f'step 3.4 : Lesion labelling, volumetry and location')
                    
                    # Pre check 
                    ## definition of variables
                    WHITE_MATTER   = 2
                    GRAY_MATTER    = 3
                    VENTRICLES     = 4
                    INFRATENTORIAL = 16 
                    
                    # Actions
                    def load_segmentations(subject, session):
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
                        aseg_img = nib.load(f'{sub_ses_derivative_path_segment}/sub-{subject}_ses-{session}_aseg_lesions.nii.gz')
                        seg = aseg_img.get_fdata()
                        
                        # Make lesion matrix from segmentations matrix
                        lesion = seg.copy()
                        lesion[lesion!=99] = 0
                        lesion[lesion==99] = 1
                        
                        return aseg_img, seg, lesion
                    
                    
                    
                    def make_lesions_csv(subject, session, minimum_lesion_size=5):
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
                        image, aseg, lesion = load_segmentations(subject, session) 
                        
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
                                loc_20,_,_ = lesion_location(subject, session, lesion_id, lesion_mx=labeled_lesions,
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
                        df.to_csv(pjoin(sub_ses_derivative_path_stats, f'sub-{self.sub}_ses-{self.ses}_lesions.csv'), index=False)
                        
                        # Save the lesion mask with labels to a nifti file
                        labeled_lesions_nifti = nib.Nifti1Image(labeled_lesions, affine=image.affine, header=image.header)
                        # nib.save(labeled_lesions_nifti, pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_labeled_lesions.nii.gz'))
                        
                        
                          
                    def lesion_location(subject, session, lesion_label, lesion_mx=None, aseg_mx=None, percentage=0.2):
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
                            lesion_image = nib.load(f'{sub_ses_derivative_path_segment}/sub-{subject}_ses-{session}_labeled_lesions.nii.gz')
                            lesion_mx = lesion_image.get_fdata()
                            
                        if aseg_mx is None:
                            # Load segmentation
                            aseg_image = nib.load(f'{sub_ses_derivative_path_segment}/sub-{subject}_ses-{session}_aseg.nii.gz')
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
                        
                        
                        
                    def make_location_mask(subject, session, percentage=20):
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
                        df = pd.read_csv(f'{sub_ses_derivative_path_stats}/sub-{subject}_ses-{session}_lesions.csv')
                        locations = list(df["Location"]) # {0}%".format(percentage)])
                        ids = list(df["lesion_id"])
                        
                        lesion_image = nib.load(f'{sub_ses_derivative_path_segment}/sub-{subject}_ses-{session}_labeled_lesions.nii.gz')
                        lesion_mx = lesion_image.get_fdata()
                        
                        lesion_loc = lesion_mx.copy()
                        
                        dictionary = {"White Matter":100, "Cortical or juxta-cortical":200, "Periventricular":300, "Infratentorial":400}
                        
                        for i in range(len(locations)):
                            lesion_loc[lesion_loc == ids[i]] = dictionary[locations[i]]
                        
                        lesion_loc_nifti = nib.Nifti1Image(lesion_loc, affine=lesion_image.affine, header=lesion_image.header)
                        # nib.save(lesion_loc_nifti, f'{sub_ses_derivative_path_segment}/sub-{subject}_ses-{session}_lesion_locations.nii.gz')
                    
                        
                        
                    # Setp 3.4: Lesion labelling, volumetry and location
                    
                    # Pre check 
                    ## check if files exist
                    if not pexists(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg_lesions.nii.gz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg_lesions.nii.gz" not Found !')
                        return 
                    
                    # Actions 
                    try:
                        print('Setp 3.4: make_lesion_csv')
                        make_lesions_csv(self.sub, self.ses)
                    except Exception as e:
                        print(f'[ERROR] - {self.pipeline} | {e} while make_lesion_csv')
                        return
                    
                    # Pre check 
                    ## check if files exist
                    if not pexists(f'{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}_lesions.csv'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}_lesions.csv" not Found !')
                        return 
                    
                    if not pexists(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_labeled_lesions.nii.gz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_labeled_lesions.nii.gz" not Found !')
                        return 
                    
                    # Actions 
                    try:
                        print('Setp 3.4: make_location_mask')
                        make_location_mask(self.sub, self.ses, 20)
                    except Exception as e:
                        print(f'[ERROR] - {self.pipeline} | {e} while make_location_mask')
                        return
                    
                    
                    # Step 3.5 : Recompute Freesurfer volumetry based on the new segmentation file
                    print('Step 3.5 : Recompute Freesurfer volumetry based on the new segmentation file')
                    
                    # Pre check
                    ## check if files exist
                    if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz" not Found !')
                        return 
                    
                    # Actions
                    ## Converting mri/aseg_lesions.nii.gz --> mri/aseg_lesion.mgz to use it in freesurfer        
                    try:
                        print(f'Converting mri/aseg_lesions.nii.gz --> mri/aseg_lesion.mgz to use it in freesurfer ')
                        
                        # subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz', shell=True).wait()
                        subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz"', shell=True).wait()
                        
                        # shutil.copy(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz', f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg_lesions.nii.gz')

                    except Exception as e:
                        print(f'[ERROR] - {self.pipeline} | {e} while converting mri/aseg_lesions.nii.gz --> mri/aseg_lesion.mgz')
                        return
                    
                    # Pre check
                    ## check if files exist
                    if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz" not Found !')
                        return 
                    
                    if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats" not Found !')
                        return 
                    
                    if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz" not Found !')
                        return 
                    
                    if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/brainmask.mgz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/brainmask.mgz" not Found !')
                        return 
                    
                    if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/brainmask.mgz'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/brainmask.mgz" not Found !')
                        return 
                    
                    # Actions
                    ## Executing mri_segstats on aseg_lesion.mgz
                    try:
                        print(f'Executing mri_segstats on aseg_lesion.mgz')
                        
                        # subprocess.Popen(f'mri_segstats --seed 1234 --seg {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz \
                        #                  --sum {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats --pv {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz \
                        #                    --empty --brainmask {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/brainmask.mgz --brain-vol-from-seg --excludeid 0 \
                        #                      --excl-ctxgmwm --supratent --subcortgray --in {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz \
                        #                        --in-intensity-name norm --in-intensity-units MR --etiv --surf-wm-vol --surf-ctx-vol \
                        #                          --totalgray --euler --ctab \
                        #                            /home/stluc/Programmes/freesurfer/ASegStatsLUT.txt --sd {sub_ses_fs_path} --subject sub-{self.sub}_ses-{self.ses}_MPRAGE', shell=True).wait()
                        subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_fs_path}:/media/sub_ses_fs_path -v {path_to_ref_image}:/media/path_to_ref_image -v {path_to_trans_registered_image}:/media/path_to_trans_registered_image colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_segstats --seed 1234 --seg /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz \
                                                                                                                                                                                                                                                                                                                  --sum /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats --pv /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz \
                                                                                                                                                                                                                                                                                                                    --empty --brainmask /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/brainmask.mgz --brain-vol-from-seg --excludeid 0 \
                                                                                                                                                                                                                                                                                                                      --excl-ctxgmwm --supratent --subcortgray --in /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz \
                                                                                                                                                                                                                                                                                                                        --in-intensity-name norm --in-intensity-units MR --etiv --surf-wm-vol --surf-ctx-vol \
                                                                                                                                                                                                                                                                                                                          --totalgray --euler --ctab \
                                                                                                                                                                                                                                                                                                                            /programs/freesurfer/ASegStatsLUT.txt --sd /mediasub_ses_fs_path --subject sub-{self.sub}_ses-{self.ses}_MPRAGE"', shell=True).wait()

                    except Exception as e:
                        print(f'[ERROR] - {self.pipeline} | {e} while Executing mri_segstats on aseg_lesion.mgz')
                        return
                    
                    
                    # Step 3.6 : Make subject-{self.sub}_ses-{self.ses}.csv
                    print(f'Step 3.6 : Make subject-{self.sub}_ses-{self.ses}.csv')  
                    
                    # Pre check
                    
                    # Actions            
                    def get_brain_volumes(subject, session):
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
                        
                        with open(f'{sub_ses_fs_path}/sub-{subject}_ses-{session}_MPRAGE/stats/aseg_lesions.stats') as file:
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
                        
                        
                    def get_lesions_information(subject, session, stats):
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
                        
                        df = pd.read_csv(f'{sub_ses_derivative_path_stats}/sub-{subject}_ses-{session}_lesions.csv')
                        
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
                        
                        
                    
                    def make_subject_csv(subject, session):
                        
                        stats = get_brain_volumes(subject, session)
                        stats, wm_lesions = get_lesions_information(subject, session, stats)
                        
                        ic_volume = stats['Intracranial volume']
                        
                        stats['White matter'] = stats['White matter'] + stats['WM-hypointenisities'] 
                        stats['Total lesion volume'] = stats['Total lesion volume'] / ic_volume 
                        
                        df = pd.DataFrame.from_dict(stats, orient='index', columns = [subject])
                        df = df.transpose()
                        df.to_csv(f'{sub_ses_derivative_path_stats}/sub-{subject}_ses-{session}_volumetry.csv')
                        
                    # Step 3.6 
                    
                    # Pre check
                    ## check if files exist
                    if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats" not Found !')
                        return 
                    
                    if not pexists(f'{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}_lesions.csv'):
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}_lesions.csv" not Found !')
                        return 
                    
                    # Actions
                    try:
                        print('make_subject_csv')
                        make_subject_csv(self.sub, self.ses)
                    except Exception as e:
                        print('[ERROR] - {self.pipeline} | {e} while make_subject_csv¸')
                    
                    print('End Localizing and computing volumetry of the lesions!')
                            
                print('LesVolLoc end')
                    
                
                print(f'LesVolLoc has processed sub-{sub} ses-{ses}')
        self.finished.emit()
    
    def run_LesVolLoc_2(self):
        time.sleep(100)
  
    def run_LesVolLoc(self): 
        
        # Define paths and filenames for a certain SUBJECT and SESSION
        fs = 'FreeSurfer'
        derivative = 'LesVolLoc'
        samseg = 'SAMSEG'
        segment = 'segmentation'
        transfo = 'transformation'
        sub_ses_directory = pjoin(self.bids.root_dir, f'sub-{self.sub}', f'ses-{self.ses}', 'anat')
        flair = f'sub-{self.sub}_ses-{self.ses}_FLAIR.nii.gz'
        mprage = f'sub-{self.sub}_ses-{self.ses}_acq-MPRAGE_T1w.nii.gz'
        sub_ses_derivative_path_segment = pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, segment)
        sub_ses_derivative_path_transfo = pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, transfo)
        sub_ses_derivative_path_stats = pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, 'stats')
        sub_ses_fs_path = pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', fs)
        
        # Define list of directories to create
        directorysegment = [pjoin('derivatives', derivative), pjoin('derivatives', derivative, f'sub-{self.sub}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, segment)]
        directorytransfo = [pjoin('derivatives', derivative), pjoin('derivatives', derivative, f'sub-{self.sub}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, transfo)]
        directorystats = [pjoin('derivatives', derivative), pjoin('derivatives', derivative, f'sub-{self.sub}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}'), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg), pjoin('derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', samseg, 'stats')]
        directory_fs_sub_ses = [pjoin('derivatives', derivative), pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}'), pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}'), pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{self.sub}', f'ses-{self.ses}', fs)]
        
        # Perform Lesion Segmentation, Localisation and Volumetry
        
        ## Step1 : Preprocessing (normalization and registration FLAIR and MPRAGE)
        if self.step1 == True: 
            
            print('Start Preprocessing...')
            
            # Pre check
            ## Create corresponding directory if necessary
            self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = directorytransfo)
            
            # Actions
            ## Normalization if need 
            if self.normalization == True:
                
                print('normalization')
                
                # Pre check
                ## check if preprocessing has already been done previously, and delete the results if necessary
                if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed')):
                    shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed'))
                if pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz')):
                    os.remove(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz'))
                    
                ## check if files exist
                if not pexists(pjoin(sub_ses_directory, flair)):
                    print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, flair)}" not Found !')
                    return
                
                # Actions
                ## Normalized FLAIR
                try:
                    print(f'Resizing FLAIR for sub-{self.sub} ses-{self.ses}...')
                    
                    # subprocess.Popen(f'recon-all -motioncor -i {sub_ses_directory}/{flair} -subjid sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed -sd {sub_ses_derivative_path_transfo}', shell=True).wait()
                    subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_directory}:/media/sub_ses_directory -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && recon-all -motioncor -i /media/sub_ses_directory/{flair} -subjid sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed -sd /media/sub_ses_derivative_path_transfo"', shell=True).wait()
                    
                except Exception as e:
                    print(f'[ERROR] - {self.pipeline} | {e} when resizing FLAIR for sub-{self.sub}_ses-{self.ses}!')
                    return
                
                ## Convert mgz file from freesurfer to nii file 
                try:
                    print(f'Converting FLAIR_used.mgz to .nii.gz for sub-{self.sub} ses-{self.ses}...')
                    
                    # subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed/mri/orig.mgz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz', shell=True).wait()
                    subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed/mri/orig.mgz /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz"', shell=True).wait()           
                    
                except Exception as e:
                    print(f'[ERROR] - {self.pipeline} | {e} when converting FLAIR_used.mgz to .nii.gz for sub-{self.sub}_ses{self.ses}!')
                    return
                
            ## No normalization
            else: 
            
                print('No Normalization !')
                
                # Pre check
                ## check if preprocessing has already been done previously, and delete the results if necessary
                if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed')):
                    shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed'))
                if pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz')):
                    os.remove(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz'))
                    
                ## check if files exist
                if not pexists(pjoin(sub_ses_directory, flair)):
                    print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, flair)}" not Found !')
                    return
                
                # Actions
                ## Copy FLAIR in directory of transformations for access simplicity
                shutil.copyfile(pjoin(sub_ses_directory, flair), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz'))
            
            ## Register MPRAGE on FLAIR
            if self.mprage == True:
                
                print('Preprocessing mprage...')
                
                # Pre check
                ## check if files exist
                if not pexists(pjoin(sub_ses_directory, flair)):
                    print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, flair)}" not Found !')
                    return
                
                if not pexists(pjoin(sub_ses_directory, mprage)):
                    print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, mprage)}" not Found !')
                    return
                
                
                # Actions
                ## Resgistering MPRAGE on FLAIR
                try:
                    print(f'Registration of MPRAGE on FLAIR_preprocessed for sub-{self.sub} ses-{self.ses}...')
                                         
                    # subprocess.Popen(f'$ANTs_registration -d 3 -n 4 -f {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz -m {sub_ses_directory}/{mprage} -t r -o {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed', shell=True).wait()
                    subprocess.Popen(f'docker run --rm --privileged -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_directory}:/media/sub_ses_directory colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && \$ANTs_registration -d 3 -n 4 -f /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz -m /media/sub_ses_directory/{mprage} -t r -o /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed"', shell=True).wait()           
                    
                    # Change the name of registration output
                    shutil.move(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessedWarped.nii.gz'), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz'))
                
                except Exception as e:
                    print(f'[ERROR] - {self.pipeline} | {e} during registration of MPRAGE on FLAIR_used for sub-{self.sub}_ses{self.ses}!')
                    return
                
            else:
                pass
            
            print('End Preprocessing!')
               
        else:
            pass
        
        
        ## Step2 : Segmentation using SAMSEG to compute lesion probability mask
        if self.step2 == True:
            
            print('Start Segmentating lesions with SAMSEG...')
            
            # Pre check
            ## Create segmentation directories
            self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = directorysegment)     
            self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = [f'{sub_ses_derivative_path_segment}/SAMSEG_results'])
            
            # Actions
            ## Run SAMSEG with FLAIR and MPRAGE
            if self.mprage == True:
                
                print('Segmenting with FLAIR & mprage')
                
                # Pre check
                ## check if files exist
                if not pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz')):
                    file = pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz')
                    print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{file}" not Found !')
                    return
                
                if not pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz')):
                    file = pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz')
                    print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{file}" not Found !')
                    return
                
                # Actions
                try:
                    print(f'Running Samseg for sub-{self.sub} ses-{self.ses}...')
                    
                    # subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz', shell=True).wait()
                    subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz"', shell=True).wait()
                    
                    # subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.mgz', shell=True).wait()
                    subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.mgz"', shell=True).wait()
                    
                    # subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.mgz -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz --lesion --lesion-mask-pattern 0 1 --threads 4 -o {sub_ses_derivative_path_segment}/SAMSEG_results --save-posteriors', shell=True).wait()
                    subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && run_samseg -i /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.mgz -i /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz --lesion --lesion-mask-pattern 0 1 --threads 4 -o /media/sub_ses_derivative_path_segment/SAMSEG_results --save-posteriors"', shell=True).wait()
                    
                    # subprocess.Popen(f'mri_convert {sub_ses_derivative_path_segment}/SAMSEG_results/posteriors/Lesions.mgz {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz', shell=True).wait()
                    subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_segment/SAMSEG_results/posteriors/Lesions.mgz /media/sub_ses_derivative_path_segment/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz"', shell=True).wait()
                    
                except Exception as e:
                    print(f'[ERROR] - {self.pipeline} | {e} while running Samseg for sub-{self.sub}_ses{self.ses}!')
                    return
                
            ## Run SAMSEG with only FLAIR 
            else:
                
                print('Segmenting with only FLAIR')
                
                # Pre check
                ## check if files exist
                if not pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz')):
                    file = pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz')
                    print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{file}" not Found !')
                    return
                
                # Actions
                try:
                    print(f'Running Samseg for sub-{self.sub} ses-{self.ses}...')

                    # subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz', shell=True).wait()
                    subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz"', shell=True).wait()
                    
                    # subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o {sub_ses_derivative_path_segment}/SAMSEG_results --save-posteriors', shell=True).wait()
                    subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && run_samseg -i /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o /media/sub_ses_derivative_path_segment/SAMSEG_results --save-posteriors"', shell=True).wait()
                    
                    # subprocess.Popen(f'mri_convert {sub_ses_derivative_path_segment}/SAMSEG_result/posteriors/Lesions.mgz {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz', shell=True).wait()
                    subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_segment/SAMSEG_result/posteriors/Lesions.mgz /media/sub_ses_derivative_path_segment/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz"', shell=True).wait()
                    
                except Exception as e:   
                    print(f'[ERROR] - {self.pipeline} | {e} while running Samseg for sub-{self.sub}_ses{self.ses}!')
                    return
                
            ## Binarizing the lesion probability  mask    
            # Pre check
            ## check if files exist
            if not pexists(pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_lesions.nii.gz')):
                file = pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_lesions.nii.gz')
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{file}" not Found !')
                return
            
            try:                
                # Actions
                print(f'Binarizing lesion probability mask for sub-{self.sub} ses-{self.ses}...')
               
                threshold = 0.5
                image = nib.load(pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_lesions.nii.gz'))
                lesions = image.get_fdata()
                lesions[lesions >= threshold] = 1
                lesions[lesions < threshold] = 0
            
                lesions_nifti = nib.Nifti1Image(lesions, affine=image.affine)
                nib.save(lesions_nifti, pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz'))
                
            except Exception as e:
                print(f'[ERROR] - {self.pipeline} | {e} while binarizing lesion probability mask for sub-{self.sub}_ses{self.ses}!')
                return
            
            print('End SAMSEG!')
                   
        ## Run recon-all for volumetry
        if self.recon_all:
            
            print('Start computing volumetry with recon-all...')
            
            # Pre check
            ## Create FreeSurfer directory
            self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories=directory_fs_sub_ses)
            
            ## check if files exist
            if not pexists(pjoin(sub_ses_directory, mprage)):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, flair)}" not Found !')
                return
            
            # Actions
            try: 
                # subprocess.Popen(f'recon-all -all -i {sub_ses_directory}/{mprage} -subjid sub-{self.sub}_ses-{self.ses}_MPRAGE -sd {sub_ses_fs_path}', shell=True).wait()
                subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_directory}:/media/sub_ses_directory -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && recon-all -all -i /media/sub_ses_directory/{mprage} -subjid sub-{self.sub}_ses-{self.ses}_MPRAGE -sd /media/sub_ses_fs_path"', shell=True).wait()
                
            except Exception as e:
                print(f'[ERROR] - {self.pipeline} | {e} while computing volumetry with recon-all for sub-{self.sub}_ses{self.ses}!')
                return
            
            print('End recon-all!')
        
        ## Merge SAMSEG and FreeSurfer Results for lesion volumetry and localization
        if self.step3 == True:
            
            print('Start Localizing and computing volumetry of the lesions...')  
            
            # Pre Check
            ## Create stats directory
            self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories=directorystats)
            
            # Actions
            ## Transform the Freesurfer segmentation (product of recon-all) into the normalized space (Samseg space)
        
            print(f'step 3.1 : Transform the Freesurfer segmentation (product of recon-all) into the normalized space (Samseg space)')
            
            # Pre check
            ## check if files exist
            if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.mgz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.mgz" not Found !')
                return
            
            if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.mgz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.mgz" not Found !')
                return
            
            if not pexists(f'{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz" not Found !')
                return       
            
            # Actions 
            ## convert orig/aseg.mgz -> nii.gz            
            try:
                print(f'mri/orig.mgz --> mri/orig.nii.gz and mri/aseg.mgz --> mri.aseg.nii.gz')
                
                # subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.mgz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz', shell=True).wait()
                subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.mgz /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz"', shell=True).wait()
                
                # subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.mgz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz', shell=True).wait()
                subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.mgz /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz"', shell=True).wait()

            except Exception as e:
                print(f'[ERROR] - {self.pipeline} | {e} while converting mri/orig.mgz --> mri/orig.nii.gz and/or mri/aseg.mgz --> mri.aseg.nii.gz')
                return
            
            ## Registration of orig to MPRAGE_preprocessed            
            try:
                print(f'Registration Orig on MPRAGE_preprocessed')
                
                # subprocess.Popen(f'$ANTs_registration -d 3 -n 4 -f {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz -m {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -t r -o {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed', shell=True).wait()
                subprocess.Popen(f'docker run --rm --privileged -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && \$ANTs_registration -d 3 -n 4 -f /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz -m /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -t r -o /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed"', shell=True).wait()

            except Exception as e:
                print(f'[ERROR] - {self.pipeline} | {e} while registrating Orig on MPRAGE_preprocessed')
                return
            
            ## Registration of aseg to MPRAGE_preprocessed
            try:
                print(f'Registration aseg on MPRAGE_preprocessed')
                
                # subprocess.Popen(f'$ANTSPATH/antsApplyTransforms -d 3 -i {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz -r {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz -n GenericLabel -t {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat -o {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg.nii.gz', shell=True).wait()
                subprocess.Popen(f'docker run --rm --privileged -v {sub_ses_fs_path}:/media/sub_ses_fs_path -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && \$ANTs_applyTransforms -d 3 -i /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz -r /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz -n GenericLabel -t /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat -o /media/sub_ses_derivative_path_segment/sub-{self.sub}_ses-{self.ses}_aseg.nii.gz"', shell=True).wait()
                
            except Exception as e:
                print(f'[ERROR] - {self.pipeline} | {e} while registrating aseg on MPRAGE_used')
                return
            
            print(f'step 3.2 : Transform de binarized lesion mask (product of Samseg) into freesurfer space')
            
            # Pre check
            ## check if files exist
            if not pexists(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz" not Found !')
                return    
            
            if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz" not Found !')
                return     
            
            if not pexists(f'{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat" not Found !')
                return 
            
            if not pexists(f'{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz" not Found !')
                return    
            
            # Actions
            ## Transforming the binarized lesion mask (product of Samseg) into freesurfer space
            try:
                logging.info(f'Transforming the binarized lesion mask (product of Samseg) into freesurfer space')
                
                # subprocess.Popen(f'$ANTSPATH/antsApplyTransforms -d 3 -i {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz -r {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -n GenericLabel -t [{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat, 1] -o {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz', shell=True).wait()
                subprocess.Popen(f'docker run --rm --privileged -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment -v {sub_ses_fs_path}:/media/sub_ses_fs_path -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && \$ANTs_applyTransforms -d 3 -i /media/sub_ses_derivative_path_segment/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz -r /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -n GenericLabel -t [/media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat, 1] -o /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz"', shell=True).wait()
                
                # subprocess.Popen(f'$ANTSPATH/antsApplyTransforms -d 3 -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz -r {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -n GenericLabel -t [{sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat, 1] -o {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.nii.gz', shell=True).wait()
                subprocess.Popen(f'docker run --rm --privileged -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && \$ANTs_applyTransforms -d 3 -i /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz -r /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/orig.nii.gz -n GenericLabel -t [/media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_ORIG_to_MPRAGE_preprocessed0GenericAffine.mat, 1] -o /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.nii.gz"', shell=True).wait()
                
                # subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.mgz', shell=True).wait()
                subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.mgz"', shell=True).wait()
                
                # subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.nii.gz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.mgz', shell=True).wait()
                subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.nii.gz /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/FLAIR.mgz"', shell=True).wait()

            except Exception as e:
                print(f'[ERROR] - {self.pipeline} | {e} while transforming the binarized lesion mask (product of Samseg) into freesurfer space')
                return
            
            print(f'step 3.3 : Merge the brain segmentation files with the lesion masks in both samseg and Freesurfer spaces')
            
            # Pre check
            
            # Actions            
            def update_aseg_norm(subject, session, path):
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
                lesion_image = nib.load(f'{path}/sub-{subject}_ses-{session}_lesions_binary.nii.gz')
                lesion_mx = lesion_image.get_fdata()
                
                lesion_mask = ma.masked_not_equal(lesion_mx,1)

                # Load Freesurfer segmentation mask (aseg)
                aseg_image = nib.load(f'{path}/sub-{subject}_ses-{session}_aseg.nii.gz')
                aseg_mx = aseg_image.get_fdata()
                
                # Set all voxels of aseg marked as lesion in the lesion mask to 99 (Freesurfer lesion id)
                aseg_mask = ma.masked_array(aseg_mx, np.logical_not(lesion_mask.mask), fill_value=99).filled()

                # Save resulting matrix to nifti file
                aseg_norm_nifti = nib.Nifti1Image(aseg_mask, affine=aseg_image.affine)

                nib.save(aseg_norm_nifti, f'{path}/sub-{subject}_ses-{session}_aseg_lesions.nii.gz')


                
            def update_aseg_fs(subject, session, path):
                
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
                lesion_image = nib.load(f'{path}/sub-{subject}_ses-{session}_MPRAGE/mri/lesions_fs.nii.gz')
                lesion_mx = lesion_image.get_fdata()
                
                lesion_mask = ma.masked_not_equal(lesion_mx,1)
                
                # Loa Freesurfer segmentation mask (aseg)
                aseg_image = nib.load(f'{path}/sub-{subject}_ses-{session}_MPRAGE/mri/aseg.nii.gz')
                aseg_mx = aseg_image.get_fdata()
                
                # Set all voxels of aseg marked as lesion in the lesion ask to 99 (Freesurfer lesion id)
                aseg_mask = ma.masked_array(aseg_mx, np.logical_not(lesion_mask.mask), fill_value=99).filled()
                
                # Save resulting matrix to nifti file
                aseg_fs_nifti = nib.Nifti1Image(aseg_mask, affine=aseg_image.affine)
                nib.save(aseg_fs_nifti, f'{path}/sub-{subject}_ses-{session}_MPRAGE/mri/aseg_lesions.nii.gz')

            
            
            def update_aseg(subject, session, path_fs, path_norm):
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
                update_aseg_norm(subject, session, path_norm)
                update_aseg_fs(subject, session, path_fs)
                
            # Step 3.3: Merge the brain segmentation files with the lesion masks in both samseg and Freesurfer spaces
            
            # Pre check
            ## check if files exist
            if not pexists(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz" not Found !')
                return 
            
            if not pexists(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg.nii.gz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg.nii.gz" not Found !')
                return 
            
            if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/lesions_fs.nii.gz" not Found !')
                return 
            
            if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg.nii.gz" not Found !')
                return 
            
            # Actions
            try:
                update_aseg(self.sub, self.ses, sub_ses_fs_path, sub_ses_derivative_path_segment)
            except Exception as e:
                print(f'[ERROR] - {self.pipeline} | {e} while merging brain segmentation files sith the lesion masks in both samseg and freesurfer space')
            
            # Setp 3.4: Lesion labelling, volumetry and location
            print(f'step 3.4 : Lesion labelling, volumetry and location')
            
            # Pre check 
            ## definition of variables
            WHITE_MATTER   = 2
            GRAY_MATTER    = 3
            VENTRICLES     = 4
            INFRATENTORIAL = 16 
            
            # Actions
            def load_segmentations(subject, session):
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
                aseg_img = nib.load(f'{sub_ses_derivative_path_segment}/sub-{subject}_ses-{session}_aseg_lesions.nii.gz')
                seg = aseg_img.get_fdata()
                
                # Make lesion matrix from segmentations matrix
                lesion = seg.copy()
                lesion[lesion!=99] = 0
                lesion[lesion==99] = 1
                
                return aseg_img, seg, lesion
            
            
            
            def make_lesions_csv(subject, session, minimum_lesion_size=5):
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
                image, aseg, lesion = load_segmentations(subject, session) 
                
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
                        loc_20,_,_ = lesion_location(subject, session, lesion_id, lesion_mx=labeled_lesions,
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
                df.to_csv(pjoin(sub_ses_derivative_path_stats, f'sub-{self.sub}_ses-{self.ses}_lesions.csv'), index=False)
                
                # Save the lesion mask with labels to a nifti file
                labeled_lesions_nifti = nib.Nifti1Image(labeled_lesions, affine=image.affine, header=image.header)
                nib.save(labeled_lesions_nifti, pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_labeled_lesions.nii.gz'))
                
                
                  
            def lesion_location(subject, session, lesion_label, lesion_mx=None, aseg_mx=None, percentage=0.2):
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
                    lesion_image = nib.load(f'{sub_ses_derivative_path_segment}/sub-{subject}_ses-{session}_labeled_lesions.nii.gz')
                    lesion_mx = lesion_image.get_fdata()
                    
                if aseg_mx is None:
                    # Load segmentation
                    aseg_image = nib.load(f'{sub_ses_derivative_path_segment}/sub-{subject}_ses-{session}_aseg.nii.gz')
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
                
                
                
            def make_location_mask(subject, session, percentage=20):
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
                df = pd.read_csv(f'{sub_ses_derivative_path_stats}/sub-{subject}_ses-{session}_lesions.csv')
                locations = list(df["Location"]) # {0}%".format(percentage)])
                ids = list(df["lesion_id"])
                
                lesion_image = nib.load(f'{sub_ses_derivative_path_segment}/sub-{subject}_ses-{session}_labeled_lesions.nii.gz')
                lesion_mx = lesion_image.get_fdata()
                
                lesion_loc = lesion_mx.copy()
                
                dictionary = {"White Matter":100, "Cortical or juxta-cortical":200, "Periventricular":300, "Infratentorial":400}
                
                for i in range(len(locations)):
                    lesion_loc[lesion_loc == ids[i]] = dictionary[locations[i]]
                
                lesion_loc_nifti = nib.Nifti1Image(lesion_loc, affine=lesion_image.affine, header=lesion_image.header)
                nib.save(lesion_loc_nifti, f'{sub_ses_derivative_path_segment}/sub-{subject}_ses-{session}_lesion_locations.nii.gz')
            
                
                
            # Setp 3.4: Lesion labelling, volumetry and location
            
            # Pre check 
            ## check if files exist
            if not pexists(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg_lesions.nii.gz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg_lesions.nii.gz" not Found !')
                return 
            
            # Actions 
            try:
                print('Setp 3.4: make_lesion_csv')
                make_lesions_csv(self.sub, self.ses)
            except Exception as e:
                print(f'[ERROR] - {self.pipeline} | {e} while make_lesion_csv')
                return
            
            # Pre check 
            ## check if files exist
            if not pexists(f'{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}_lesions.csv'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}_lesions.csv" not Found !')
                return 
            
            if not pexists(f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_labeled_lesions.nii.gz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_labeled_lesions.nii.gz" not Found !')
                return 
            
            # Actions 
            try:
                print('Setp 3.4: make_location_mask')
                make_location_mask(self.sub, self.ses, 20)
            except Exception as e:
                print(f'[ERROR] - {self.pipeline} | {e} while make_location_mask')
                return
            
            
            # Step 3.5 : Recompute Freesurfer volumetry based on the new segmentation file
            print('Step 3.5 : Recompute Freesurfer volumetry based on the new segmentation file')
            
            # Pre check
            ## check if files exist
            if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz" not Found !')
                return 
            
            # Actions
            ## Converting mri/aseg_lesions.nii.gz --> mri/aseg_lesion.mgz to use it in freesurfer        
            try:
                print(f'Converting mri/aseg_lesions.nii.gz --> mri/aseg_lesion.mgz to use it in freesurfer ')
                
                # subprocess.Popen(f'mri_convert {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz', shell=True).wait()
                subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_fs_path}:/media/sub_ses_fs_path colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz"', shell=True).wait()
                
                # shutil.copy(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.nii.gz', f'{sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_aseg_lesions.nii.gz')

            except Exception as e:
                print(f'[ERROR] - {self.pipeline} | {e} while converting mri/aseg_lesions.nii.gz --> mri/aseg_lesion.mgz')
                return
            
            # Pre check
            ## check if files exist
            if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz" not Found !')
                return 
            
            if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats" not Found !')
                return 
            
            if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz" not Found !')
                return 
            
            if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/brainmask.mgz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/brainmask.mgz" not Found !')
                return 
            
            if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/brainmask.mgz'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/brainmask.mgz" not Found !')
                return 
            
            # Actions
            ## Executing mri_segstats on aseg_lesion.mgz
            try:
                print(f'Executing mri_segstats on aseg_lesion.mgz')
                
                # subprocess.Popen(f'mri_segstats --seed 1234 --seg {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz \
                #                  --sum {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats --pv {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz \
                #                    --empty --brainmask {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/brainmask.mgz --brain-vol-from-seg --excludeid 0 \
                #                      --excl-ctxgmwm --supratent --subcortgray --in {sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz \
                #                        --in-intensity-name norm --in-intensity-units MR --etiv --surf-wm-vol --surf-ctx-vol \
                #                          --totalgray --euler --ctab \
                #                            /home/stluc/Programmes/freesurfer/ASegStatsLUT.txt --sd {sub_ses_fs_path} --subject sub-{self.sub}_ses-{self.ses}_MPRAGE', shell=True).wait()
                subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_fs_path}:/media/sub_ses_fs_path -v {path_to_ref_image}:/media/path_to_ref_image -v {path_to_trans_registered_image}:/media/path_to_trans_registered_image colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_segstats --seed 1234 --seg /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/aseg_lesions.mgz \
                                                                                                                                                                                                                                                                                                          --sum /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats --pv /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz \
                                                                                                                                                                                                                                                                                                            --empty --brainmask /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/brainmask.mgz --brain-vol-from-seg --excludeid 0 \
                                                                                                                                                                                                                                                                                                              --excl-ctxgmwm --supratent --subcortgray --in /media/sub_ses_fs_path/sub-{self.sub}_ses-{self.ses}_MPRAGE/mri/norm.mgz \
                                                                                                                                                                                                                                                                                                                --in-intensity-name norm --in-intensity-units MR --etiv --surf-wm-vol --surf-ctx-vol \
                                                                                                                                                                                                                                                                                                                  --totalgray --euler --ctab \
                                                                                                                                                                                                                                                                                                                    /programs/freesurfer/ASegStatsLUT.txt --sd /mediasub_ses_fs_path --subject sub-{self.sub}_ses-{self.ses}_MPRAGE"', shell=True).wait()

            except Exception as e:
                print(f'[ERROR] - {self.pipeline} | {e} while Executing mri_segstats on aseg_lesion.mgz')
                return
            
            
            # Step 3.6 : Make subject-{self.sub}_ses-{self.ses}.csv
            print(f'Step 3.6 : Make subject-{self.sub}_ses-{self.ses}.csv')  
            
            # Pre check
            
            # Actions            
            def get_brain_volumes(subject, session):
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
                
                with open(f'{sub_ses_fs_path}/sub-{subject}_ses-{session}_MPRAGE/stats/aseg_lesions.stats') as file:
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
                
                
            def get_lesions_information(subject, session, stats):
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
                
                df = pd.read_csv(f'{sub_ses_derivative_path_stats}/sub-{subject}_ses-{session}_lesions.csv')
                
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
                
                
            
            def make_subject_csv(subject, session):
                
                stats = get_brain_volumes(subject, session)
                stats, wm_lesions = get_lesions_information(subject, session, stats)
                
                ic_volume = stats['Intracranial volume']
                
                stats['White matter'] = stats['White matter'] + stats['WM-hypointenisities'] 
                stats['Total lesion volume'] = stats['Total lesion volume'] / ic_volume 
                
                df = pd.DataFrame.from_dict(stats, orient='index', columns = [subject])
                df = df.transpose()
                df.to_csv(f'{sub_ses_derivative_path_stats}/sub-{subject}_ses-{session}_volumetry.csv')
                
            # Step 3.6 
            
            # Pre check
            ## check if files exist
            if not pexists(f'{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_fs_path}/sub-{self.sub}_ses-{self.ses}_MPRAGE/stats/aseg_lesions.stats" not Found !')
                return 
            
            if not pexists(f'{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}_lesions.csv'):
                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{sub_ses_derivative_path_stats}/sub-{self.sub}_ses-{self.ses}_lesions.csv" not Found !')
                return 
            
            # Actions
            try:
                print('make_subject_csv')
                make_subject_csv(self.sub, self.ses)
            except Exception as e:
                print('[ERROR] - {self.pipeline} | {e} while make_subject_csv¸')
            
            print('End Localizing and computing volumetry of the lesions!')
                    
        print('LesVolLoc end')
            