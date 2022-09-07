#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 10 14:25:40 2021

@author: ColinVDB
phase_unwrapping
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


# from my_logging import setup_logging
from tqdm.auto import tqdm


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

        self.setWindowTitle("Phase Unwrapping")
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.center()

        self.tab = PhaseUnwrappingTab(self)
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
class PhaseUnwrappingTab(QWidget):
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
        self.add_info = self.parent.add_info
        self.setMinimumSize(500, 200)

        self.subjects_input = QLineEdit(self)
        self.subjects_input.setPlaceholderText("Select subjects")

        self.sessions_input = QLineEdit(self)
        self.sessions_input.setPlaceholderText("Select sessions")

        self.phase_unwrapping_button = QPushButton("Phase Unwrapping")
        self.phase_unwrapping_button.clicked.connect(self.phase_unwrapping)

        layout = QVBoxLayout()
        layout.addWidget(self.subjects_input)
        layout.addWidget(self.sessions_input)
        layout.addWidget(self.phase_unwrapping_button)

        self.setLayout(layout)


    def phase_unwrapping(self):
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
        self.action = PhaseUnwrappingWorker(self.bids, self.subjects_and_sessions, phase=self.add_info.get('phase'))
        self.action.moveToThread(self.thread)
        self.thread.started.connect(self.action.run)
        self.action.in_progress.connect(self.is_in_progress)
        self.action.finished.connect(self.thread.quit)
        self.action.finished.connect(self.action.deleteLater)
        # last = (sub == self.subjects_and_sessions[-1][0] and ses == sess[-1])
        # self.thread.finished.connect(lambda last=last: self.end_pipeline(last))
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        self.parent.hide()
        
        
    def is_in_progress(self, in_progress):
        self.parent.parent.work_in_progress.update_work_in_progress(in_progress)


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
            logging.info("Phase Unwrapping Pipeline has finished working")



# =============================================================================
# FlairStarWorker
# =============================================================================
class PhaseUnwrappingWorker(QObject):
    """
    """
    finished = pyqtSignal()
    in_progress = pyqtSignal(tuple)


    def __init__(self, bids, subjects_and_sessions, phase='part-phase_acq-WRAPPED_T2starw'):
        """


        Parameters
        ----------
        bids : TYPE
            DESCRIPTION.
        sub : TYPE
            DESCRIPTION.
        ses : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        super().__init__()
        self.bids = bids
        self.subjects_and_sessions = subjects_and_sessions
        self.phase = phase
        self.client = docker.from_env()


    def run(self):
        """


        Returns
        -------
        None.

        """
        self.in_progress.emit(('phase_unwrapping',True))
        
        for sub, sess in self.subjects_and_sessions:
            for ses in sess:
                # Action
                derivative = 'phase_unwrapped'
                sub_ses_directory = pjoin(self.bids.root_dir, f'sub-{sub}', f'ses-{ses}', 'anat')
                phase_wrapped = f'sub-{sub}_ses-{ses}_{self.phase}.nii.gz'
                phase_unwrapped_output = f'sub-{sub}_ses-{ses}_part-phase_T2starw'
                phase_unwrapped = f'sub-{sub}_ses-{ses}_part-phase_T2starw_UNWRAPPED.nii.gz'
                # Create directory
                directories = [pjoin('derivatives', derivative), pjoin('derivatives', derivative, f'sub-{sub}'), pjoin('derivatives', derivative, f'sub-{sub}', f'ses-{ses}')]
                self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories=directories)
                sub_ses_derivative_path = pjoin(self.bids.root_dir, 'derivatives', derivative, f'sub-{sub}', f'ses-{ses}')
                # Perform Flair Star computation
                try:
                    logging.info(f'Phase Unwrapping for sub-{sub} ses-{ses}...')

                    subprocess.Popen(f'docker run --rm -v {sub_ses_directory}:/data blakedewey/phase_unwrap -p {phase_wrapped} -o {phase_unwrapped_output}', shell=True).wait()
                    # self.client.containers.run('blakedewey/phase_unwrap', auto_remove=True, volumes=[f'{sub_ses_directory}:/data'], command=f'-p {phase_wrapped} -o {phase_unwrapped_output}')
                    
                    shutil.move(pjoin(sub_ses_directory, phase_unwrapped), pjoin(sub_ses_derivative_path, f'sub-{sub}_ses-{ses}_part-phase_t2starw.nii.gz'))

                    logging.info(f'Phase Unwrapped for sub-{sub} ses-{ses} computed!')
                except Exception as e:
                    logging.error(f'Error {e} when Unwrapping the phase for sub-{sub}_ses{ses}!')
                
        self.in_progress.emit(('phase_unwrapping',False))
        self.finished.emit()
