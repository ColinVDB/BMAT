#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 10 14:25:40 2021

@author: ColinVDB
BIDS MANAGER GUI
"""

# import output_redirection_tools # KEEP ME !!!

import time
import sys
import os
from os.path import join as pjoin
from os.path import exists as pexists
from dicom2bids import *
import logging
from PyQt5.QtCore import (QSize,
                          Qt,
                          QModelIndex,
                          QMutex,
                          QObject,
                          QThread,
                          pyqtSignal,
                          pyqtSlot,
                          QRunnable,
                          QThreadPool,
                          QProcess,
                          QAbstractTableModel,
                          pyqtProperty,
                          QVariant,
                          QParallelAnimationGroup,
                          QPropertyAnimation,
                          QAbstractAnimation, 
                          pyqtProperty, 
                          QObject, 
                          QTextCodec, 
                          QUrl, 
                          QMetaObject)
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
                             QTextEdit,
                             QMessageBox,
                             QListWidget,
                             QTableWidget,
                             QTableWidgetItem,
                             QMenu,
                             QAction,
                             QTableView,
                             QAbstractScrollArea,
                             QTabWidget, 
                             QInputDialog,
                             QComboBox,
                             QToolButton,
                             QScrollArea,
                             QSizePolicy,
                             QFrame, 
                             QGroupBox, 
                             QSpacerItem, 
                             QCheckBox)
from PyQt5.QtGui import (QFont,
                         QIcon,
                         QTextCursor,
                         QPixmap,
                         QColor, 
                         QMovie, 
                         QPalette,
                         QCloseEvent)
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
import traceback
import threading
import subprocess
import pandas as pd
import platform
import nibabel as nib
import numpy as np
import json
from bids_validator import BIDSValidator
import faulthandler
import zipfile
import requests
from bs4 import BeautifulSoup
import markdown
from submit_job_sss import submit_job

# from config import config_dict, STDOUT_WRITE_STREAM_CONFIG, TQDM_WRITE_STREAM_CONFIG, STREAM_CONFIG_KEY_QUEUE, \
#     STREAM_CONFIG_KEY_QT_QUEUE_RECEIVER
# from my_logging import setup_logging

# faulthandler.enable()
from pkg_resources import get_distribution, DistributionNotFound
import importlib.util
try:
    from importlib.metadata import version  # Python 3.8+
except ImportError:
    from importlib_metadata import version  # For earlier versions with the backport


def is_compiled():
    return getattr(sys, 'frozen', False)


def get_executable_path():
    if is_compiled():
        # The application is frozen (compiled)
        return os.path.dirname(sys.executable)  # Path to the executable
    else:
        # The application is not compiled, return the script path
        return os.path.dirname(os.path.abspath(__file__))

    
# def is_package_installed(package_name, version=None):
#     """
#     Check if a package is installed, and optionally if a specific version is installed.

#     :param package_name: Name of the package to check
#     :param version: Specific version to check for (e.g., '1.0.0')
#     :return: True if the package (and version) is installed, False otherwise
#     """
#     print(f'{package_name=}')
#     print(f'{version=}')
#     try:
#         dist = get_distribution(package_name)
#         print(f'{dist=}')
#         if version:
#             print('check version')
#             return dist.version == version
#         else:
#             return True
#     except DistributionNotFound:
#         return False

def is_package_installed(package_name, version=None):
    """
    Check if a package is installed, and optionally if a specific version is installed.

    :param package_name: Name of the package to check
    :param version: Specific version to check for (e.g., '1.0.0')
    :return: True if the package (and version) is installed, False otherwise
    """
    try:
        spec = importlib.util.find_spec(package_name)
        if spec is None:
            print(f'Package {package_name} is not installed.')
            return False
        
        print(f'Package {package_name} is installed.')
        if version:
            print('checking version')
            try:
                installed_version = version(package_name)
                return installed_version == version_required
            except:
                return False
        return True
    except ModuleNotFoundError:
        return False

def install_package(package_name, version=None, target_dir=None):
    """
    Install a package using pip.

    :param package_name: Name of the package to install
    :param version: Specific version to install (e.g., '1.0.0')
    :param target_dir: Directory to install the package to (if specified)
    """
    if version:
        package_str = f"{package_name}=={version}"
    else:
        package_str = package_name

    if target_dir:
        subprocess.Popen(f"pip install {package_str} --target {target_dir}", shell=True).wait()
        # subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_str, '--target', target_dir])
    else:
        subprocess.Popen(f"pip install {package_str}", shell=True).wait()
        # subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_str])

def install_requirements(requirements_path):
    """
    Install packages from a requirements file.

    :param requirements_path: Path to the requirements.txt file
    """
    # Determine if the application is running in a compiled state
    # is_compiled = getattr(sys, 'frozen', False)
    target_dir = None
    if is_compiled():
        # Set the target directory for compiled applications
        file_path = get_executable_path()
        target_dir = pjoin(file_path, '_internal') # Adjust this path as needed
        
    print(f'{target_dir=}')

    with open(requirements_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Split the line into package name and version
                print(f'{line=}')
                if '==' in line:
                    package_name, version = line.split('==')
                    version = version.strip()
                else:
                    package_name = line
                    version = None
                print(f'{package_name=}')
                print(f'{version=}')
                # Check if the package is already installed
                if not is_package_installed(package_name, version):
                    print(f"Installing {package_name}=={version}...")
                    install_package(package_name, version, target_dir)
                else:
                    print(f"{package_name}=={version} is already installed.")

def get_server_info():
    
    bmat_path = os.path.dirname(os.path.abspath(__file__))
    
    server_info = None
    with open(pjoin(bmat_path, 'server_info.json'), 'r') as f:
        server_info = json.load(f)
        
    if server_info == None:
        print('[ERROR] while loading server_info.json file')
    
    return server_info

# =============================================================================
# MainWindow
# =============================================================================
class MainWindow(QMainWindow):
    """
    Main Window of the application
    """


    def __init__(self):
        """
        Create an instance of the the Main Window

        Returns
        -------
        None.

        """
        super().__init__()
        self.memory = {}
        try:
            memory_df = pd.read_pickle('memory.xz')
            self.memory = memory_df.to_dict()
            for key in self.memory.keys():
                self.memory[key] = self.memory[key][0]
            if self.memory.get('dcm2niix_path') == None:
                self.memory['dcm2niix_path'] = ""
            if self.memory.get('itksnap') == None:
                self.memory['itksnap'] = ""
        except FileNotFoundError:
            memory_df = {'dcm2niix_path':None, 'itksnap':None}
            self.memory = memory_df
        self.system = platform.system()
        
        print(f'Is the application compiled ? {is_compiled()}')
        
        print(os.getcwd())

        self.pipelines = {}
        self.pipelines_name = []
        self.bmat_path = get_executable_path()
        print(self.bmat_path)
        
        if os.path.isdir(self.bmat_path):
            sys.path.append(pjoin(self.bmat_path))
        
        # if os.path.isdir('Pipelines'):
        #     for root, dirs, _ in os.walk('Pipelines'):
        #         for d in dirs:
        #             if d == 'src':
        #                 for file in os.listdir(pjoin(root,d)):
        #                     if os.path.isfile(pjoin(root, d, file)):
        #                         if '.json' in file:
        #                             import_r = pjoin(root, d).replace(os.sep,'.')
        #                             f = open(pjoin(root, d, file))
        #                             jsn = json.load(f)
        #                             if jsn.get('name') == None or jsn.get('source_code') == None or jsn.get('import_name') == None or jsn.get('attr') == None:
        #                                 continue
        #                             self.pipelines_name.append(jsn.get('name'))
        #                             import_name = jsn.get('import_name')
        #                             attr = jsn.get('attr')
        #                             self.pipelines[jsn.get('name')] = jsn
        #                             self.pipelines[jsn.get('name')]['import'] = __import__(f'{import_r}.{import_name}', globals(), locals(), [attr], 0)
        #                             f.close()
        if os.path.isdir(pjoin(self.bmat_path, 'Pipelines')):
            listdirs = list(os.listdir(pjoin(self.bmat_path, 'Pipelines')))
            listdirs = sorted(listdirs, key=lambda x: x.lower())
            for dirs in listdirs:
                if os.path.isdir(pjoin(self.bmat_path, 'Pipelines', dirs)):
                    for d in os.listdir(pjoin(self.bmat_path, 'Pipelines', dirs)):
                        if d == 'src':
                            for file in os.listdir(pjoin(self.bmat_path, 'Pipelines', dirs, d)):
                                if os.path.isfile(pjoin(self.bmat_path, 'Pipelines', dirs, d, file)):
                                    if '.json' in file:
                                        f = open(pjoin(self.bmat_path, 'Pipelines', dirs, d, file))
                                        jsn = json.load(f)
                                        if jsn.get('name') == None or jsn.get('source_code') == None or jsn.get('import_name') == None or jsn.get('attr') == None:
                                            continue
                                        self.pipelines_name.append(jsn.get('name'))
                                        import_name = jsn.get('import_name')
                                        attr = jsn.get('attr')
                                        self.pipelines[jsn.get('name')] = jsn
                                        if os.path.isdir(pjoin(self.bmat_path, 'Pipelines', dirs, d)):
                                            sys.path.append(pjoin(self.bmat_path, 'Pipelines', dirs, d))
                                        self.pipelines[jsn.get('name')]['import'] = __import__(f'Pipelines.{dirs}.{d}.{import_name}', globals(), locals(), [attr], 0)
                                        f.close()

        self.local_pipelines = {}
        self.local_pipelines_name = []

        if os.path.isdir(pjoin(self.bmat_path, 'LocalPipelines')):
            listdirs = list(os.listdir(pjoin(self.bmat_path, 'LocalPipelines')))
            listdirs = sorted(listdirs, key=lambda x: x.lower())
            for dirs in listdirs:
                if os.path.isdir(pjoin(self.bmat_path, 'LocalPipelines', dirs)):
                    for file in os.listdir(pjoin(self.bmat_path, 'LocalPipelines', dirs)):
                        if '.json' in file:
                            f = open(pjoin(self.bmat_path, 'LocalPipelines', dirs, file))
                            jsn = json.load(f)
                            if jsn.get('name') == None or jsn.get('source_code') == None or jsn.get('import_name') == None or jsn.get('attr') == None:
                                continue
                            self.local_pipelines_name.append(jsn.get('name'))
                            import_name = jsn.get('import_name')
                            attr = jsn.get('attr')
                            self.local_pipelines[jsn.get('name')] = jsn
                            self.local_pipelines[jsn.get('name')]['import'] = __import__(f'LocalPipelines.{dirs}.{import_name}', globals(), locals(), [attr], 0)
                            f.close()

        # Create menu bar and add action
        self.menu_bar = self.menuBar()
        self.menu_bar.setNativeMenuBar(False)
        self.bmat_menu = self.menu_bar.addMenu('&BMAT')
        
        preferences = QAction('&Preferences', self)
        preferences.triggered.connect(self.preferences)
        self.bmat_menu.addAction(preferences)
        
        self.bids_menu = self.menu_bar.addMenu('&BIDS')
        create_bids = QAction('&Create BIDS directory', self)
        create_bids.triggered.connect(self.create_bids_directory)
        self.bids_menu.addAction(create_bids)

        change_bids = QAction('&Change BIDS directory', self)
        change_bids.triggered.connect(self.change_bids_directory)
        self.bids_menu.addAction(change_bids)

        bids_quality = QAction('&BIDS Quality Control', self)
        bids_quality.triggered.connect(self.control_bids_quality)
        self.bids_menu.addAction(bids_quality)

        dataset_description = QAction('&Update Dataset Description', self)
        dataset_description.triggered.connect(self.update_dataset_description)
        self.bids_menu.addAction(dataset_description)

        # add_password = QAction('&Add Password', self)
        # add_password.triggered.connect(self.add_password_to_bids)
        # self.bids_menu.addAction(add_password)

        # remove_password = QAction('&Remove Password', self)
        # remove_password.triggered.connect(self.remove_password_to_bids)
        # self.bids_menu.addAction(remove_password)

        self.PipelinesMenu = self.menu_bar.addMenu('&Pipelines')
        add_pipelines_action = QAction('&Add New Pipelines', self)
        add_pipelines_action.triggered.connect(self.add_new_pipelines)
        self.PipelinesMenu.addAction(add_pipelines_action)

        for pipe in self.pipelines_name:
            new_action = QAction(f'&{pipe}', self)
            new_action.triggered.connect(lambda checked, arg=pipe: self.launch_pipeline(arg))
            self.PipelinesMenu.addAction(new_action)
            
        self.local_pipelines_menu = self.menu_bar.addMenu('&Local Pipelines')        
        for pipe in self.local_pipelines_name:
            new_action = QAction(f'&{pipe}', self)
            new_action.triggered.connect(lambda checked, arg=pipe: self.launch_local_pipeline(arg))
            self.local_pipelines_menu.addAction(new_action)

        # self.threads_pool = QThreadPool.globalInstance()
        
        # self.bids_apps = {}
        # self.bids_apps_name = []

        # for root, dirs, files in os.walk('BIDS_Apps'):
        #     for file in files:
        #         if '.json' in file:
        #             f = open(pjoin(root,file))
        #             jsn = json.load(f)
        #             self.bids_apps_name.append(jsn.get('name'))
        #             import_name = jsn.get('import_name')
        #             attr = jsn.get('attr')
        #             self.bids_apps[jsn.get('name')] = jsn
        #             self.bids_apps[jsn.get('name')]['import'] = __import__(f'BIDS_apps.{import_name}', globals(), locals(), [attr], 0)
        #             f.close()
        
        # self.bids_apps_menu = self.menu_bar.addMenu('&BIDS-Apps')
        
        # add_bids_apps = QAction('&Add new BIDS-Apps', self)
        # add_bids_apps.triggered.connect(self.add_new_bids_apps)
        # self.bids_apps_menu.addAction(add_bids_apps)
        
        # for app in self.bids_apps_name:
        #     new_action = QAction(f'&{app}', self)
        #     new_action.triggered.connect(lambda checked, arg=app: self.launch_bids_apps(arg))
        #     self.bids_apps_menu.addAction(new_action)

        self.init_ui()


    def init_ui(self):
        """
        Build all the widgets composing the GUI

        Returns
        -------
        None.

        """
        self.setWindowTitle('BMAT')
        self.setWindowIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'bids_icon.png')))
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.window.closeEvent = self.closeEvent

        self.center()
        
        self.bids_dir = str(QFileDialog.getExistingDirectory(self, "Select BIDS Directory", options=QFileDialog.DontUseNativeDialog))
        while self.bids_dir=="":
            self.bids_dir = str(QFileDialog.getExistingDirectory(self, "Please, select BIDS Directory", options=QFileDialog.DontUseNativeDialog))
        # if self.bids_dir == None or self.bids_dir == "":
        #     print('bruh')
            
            
        # else:

        self.bids = BIDSHandler(root_dir=self.bids_dir)
        bids_dir_split = self.bids_dir.split('/')
        self.bids_name_dir = bids_dir_split[len(bids_dir_split)-1]
        self.dataset_description = self.bids.get_dataset_description()
        if self.dataset_description.get('Name') == None or self.dataset_description.get('Name') == '':
            self.bids_lab = QLabel(self.bids_name_dir)
        else:
            self.bids_lab = QLabel(self.dataset_description.get('Name'))
        self.bids_lab.setFont(QFont('Calibri', 30))

        self.bids_dir_view = BidsDirView(self)

        self.bids_metadata = BidsMetadata(self)

        self.bids_actions = BidsActions(self)
        
        print('memory dcm2niix', self.memory.get('dcm2niix_path'))
        if self.memory.get('dcm2niix_path') != None and self.memory.get('dcm2niix_path') != '':
            print('memory dcm2niix', self.memory.get('dcm2niix_path'))
            self.dcm2niix_path = self.memory.get('dcm2niix_path')
            self.bids.setDicom2niixPath(self.dcm2niix_path)
        else:
            self.dcm2niix_path = None

        # setup_logging(self.__class__.__name__)

        # self.__logger = logging.getLogger(self.__class__.__name__)
        # self.__logger.setLevel(logging.DEBUG)

        # self.queue_std_out = config_dict[STDOUT_WRITE_STREAM_CONFIG][STREAM_CONFIG_KEY_QUEUE]

        # self.text_edit_std_out = StdOutTextEdit(self)

        # # std out stream management
        # # create console text read thread + receiver object
        # self.thread_std_out_queue_listener = QThread()
        # self.std_out_text_receiver = config_dict[STDOUT_WRITE_STREAM_CONFIG][STREAM_CONFIG_KEY_QT_QUEUE_RECEIVER]
        # # connect receiver object to widget for text update
        # self.std_out_text_receiver.queue_std_out_element_received_signal.connect(self.text_edit_std_out.append_text)
        # # attach console text receiver to console text thread
        # self.std_out_text_receiver.moveToThread(self.thread_std_out_queue_listener)
        # # attach to start / stop methods
        # self.std_out_text_receiver.finished.connect(self.std_out_text_receiver.deleteLater)
        # self.thread_std_out_queue_listener.started.connect(self.std_out_text_receiver.run)
        # self.thread_std_out_queue_listener.finished.connect(self.thread_std_out_queue_listener.deleteLater)
        # self.thread_std_out_queue_listener.start()

        # self.excel_viewer = ExcelViewer(self)
        # self.text_viewer = TextViewer(self)
        # self.default_viewer = DefaultViewer(self)
        # self.nifti_viewer = DefaultNiftiViewer(self)

        self.viewer = DefaultViewer(self)
        
        self.work_in_progress = WorkInProgress(self)

        validator = BIDSValidator()
        if not validator.is_bids(self.bids_dir):
            logging.warning('/!\ Directory is not considered as a valid BIDS directory !!!')

        self.layout = QGridLayout()
        self.layout.addWidget(self.bids_lab, 0, 1, 1, 2)
        self.layout.addWidget(self.bids_dir_view, 0, 0, 3, 1)
        self.layout.addWidget(self.bids_metadata, 1, 1)
        self.layout.addWidget(self.bids_actions, 1, 2)
        self.layout.addWidget(self.viewer, 2, 1, 1, 2)
        self.layout.addWidget(self.work_in_progress, 3, 1, 1, 2)

        self.window.setLayout(self.layout)

        self.center()


    def center(self):
        """
        Used to center the window

        Returns
        -------
        None.

        """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


    def closeEvent(self, event):
        """
        Performs last actions to be executed to cleanly close the
        application

        Parameters
        ----------
        event : an event
            /

        Returns
        -------
        None.

        """
        memory_df = pd.DataFrame(self.memory, index=[0])
        memory_df.to_pickle('memory.xz')
        # logging.info('Stop Listener')
        # self.std_out_text_receiver.deleteLater()
        # self.std_out_text_receiver.stop()
        # self.thread_std_out_queue_listener.quit()
        # self.thread_std_out_queue_listener.wait()


    def close(self):
        """
        Performs last actions to be executed to cleanly close the
        application

        Returns
        -------
        None.

        """
        memory_df = pd.DataFrame(self.memory, index=[0])
        memory_df.to_pickle('memory.xz')
        # logging.info('Stop Listener')
        # self.std_out_text_receiver.deleteLater()
        # self.std_out_text_receiver.stop()
        # self.thread_std_out_queue_listener.quit()
        # self.thread_std_out_queue_listener.wait()


    def update_bids(self):
        pass


    def updateViewer(self, viewer, file=''):
        self.layout.removeWidget(self.viewer)
        self.viewer.deleteLater()
        if viewer == 'table':
            self.viewer.close_all()
            self.viewer.deleteLater()
            self.viewer = Table_Viewer(self)
            self.viewer.viewExcel(file)
        elif viewer == 'participants_tsv':
            self.viewer.close_all()
            self.viewer.deleteLater()
            self.viewer = ParticipantsTSV_Viewer(self)
            self.viewer.viewExcel(file)
        elif viewer == 'text':
            self.viewer.close_all()
            self.viewer.deleteLater()
            self.viewer = TextViewer(self)
            self.viewer.viewText(file)
        elif viewer == 'nifti':
            self.viewer.close_all()
            self.viewer.deleteLater()
            self.viewer = DefaultNiftiViewer(self)
            self.viewer.viewNifti(file)
        else:
            self.viewer.close_all()
            self.viewer.deleteLater()
            self.viewer = DefaultViewer(self)
            self.viewer.setLabel(file)

        self.layout.deleteLater()
        self.window.deleteLater()

        self.layout = QGridLayout()
        self.layout.addWidget(self.bids_lab, 0, 1, 1, 2)
        self.layout.addWidget(self.bids_dir_view, 0, 0, 3, 1)
        self.layout.addWidget(self.bids_metadata, 1, 1)
        self.layout.addWidget(self.bids_actions, 1, 2)
        self.layout.addWidget(self.viewer, 2, 1, 1, 2)
        self.layout.addWidget(self.work_in_progress, 3, 1, 1, 2)
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.window.setLayout(self.layout)
        self.window.setLayout(self.layout)

    
    def preferences(self):
        
        if hasattr(self, 'preferences_win'):
            self.preferences_win.deleteLater()
            del self.preferences_win
        
        self.preferences_win = PreferencesWindow(self, self.memory)
        self.preferences_win.exec_()

    def launch_pipeline(self, pipe):
        """
        Used to launch a local pipeline

        Parameters
        ----------
        pipe : a pipeline
            GUI to allow the user to run a pipeline on the database

        Returns
        -------
        None.

        """
        if self.pipelines.get(pipe) != None:
            self.pipelines[pipe]['import'].launch(self, add_info=self.pipelines[pipe]['add_info'])
            return
        
    
    def update_pipelines(self):
        self.pipelines = {}
        self.pipelines_name = []

        if os.path.isdir(pjoin(self.bmat_path, 'Pipelines')):
            for dirs in os.listdir(pjoin(self.bmat_path, 'Pipelines')):
                if os.path.isdir(pjoin(self.bmat_path, 'Pipelines', dirs)):
                    for d in os.listdir(pjoin(self.bmat_path, 'Pipelines', dirs)):
                        if d == 'src':
                            for file in os.listdir(pjoin(self.bmat_path, 'Pipelines', dirs, d)):
                                if os.path.isfile(pjoin(self.bmat_path, 'Pipelines', dirs, d, file)):
                                    if '.json' in file:
                                        f = open(pjoin(self.bmat_path, 'Pipelines', dirs, d, file))
                                        jsn = json.load(f)
                                        if jsn.get('name') == None or jsn.get('source_code') == None or jsn.get('import_name') == None or jsn.get('attr') == None:
                                            continue
                                        self.pipelines_name.append(jsn.get('name'))
                                        import_name = jsn.get('import_name')
                                        attr = jsn.get('attr')
                                        self.pipelines[jsn.get('name')] = jsn
                                        if os.path.isdir(pjoin(self.bmat_path, 'Pipelines', dirs, d)):
                                            sys.path.append(pjoin(self.bmat_path, 'Pipelines', dirs, d))
                                        self.pipelines[jsn.get('name')]['import'] = __import__(f'Pipelines.{dirs}.{d}.{import_name}', globals(), locals(), [attr], 0)
                                        f.close()
        
        # self.PipelinesMenu.deleteLater()
                                
        self.PipelinesMenu.clear()
        add_pipelines_action = QAction('&Add New Pipelines', self)
        add_pipelines_action.triggered.connect(self.add_new_pipelines)
        self.PipelinesMenu.addAction(add_pipelines_action)

        for pipe in self.pipelines_name:
            new_action = QAction(f'&{pipe}', self)
            new_action.triggered.connect(lambda checked, arg=pipe: self.launch_pipeline(arg))
            self.PipelinesMenu.addAction(new_action)


    def launch_local_pipeline(self, pipe):
        """
        Used to launch a local pipeline

        Parameters
        ----------
        pipe : a pipeline
            GUI to allow the user to run a pipeline on the database

        Returns
        -------
        None.

        """
        if self.local_pipelines.get(pipe) != None:
            self.local_pipelines[pipe]['import'].launch(self, add_info=self.local_pipelines[pipe]['add_info'])
            return


    def create_bids_directory(self):
        logging.info("update_bids!")

        bids_dir = str(QFileDialog.getExistingDirectory(self, "Create new BIDS Directory", options=QFileDialog.DontUseNativeDialog))
        if os.path.isdir(bids_dir):
            self.bids_dir = bids_dir
            self.bids = BIDSHandler(root_dir=self.bids_dir)
            bids_dir_split = self.bids_dir.split('/')
            self.bids_name = bids_dir_split[len(bids_dir_split)-1]
            self.bids_lab = QLabel(self.bids_name)
            self.bids_lab.setFont(QFont('Calibri', 30))

            self.bids_dir_view = BidsDirView(self)

            self.bids_metadata = BidsMetadata(self)

            self.bids_actions.update_bids(self)

            self.viewer = DefaultViewer(self)
            # self.work_in_progress = WorkInProgress(self)

            self.layout.deleteLater()
            self.window.deleteLater()

            self.layout = QGridLayout()
            self.layout.addWidget(self.bids_lab, 0, 1, 1, 2)
            self.layout.addWidget(self.bids_dir_view, 0, 0, 3, 1)
            self.layout.addWidget(self.bids_metadata, 1, 1)
            self.layout.addWidget(self.bids_actions, 1, 2)
            self.layout.addWidget(self.viewer, 2, 1, 1, 2)
            self.layout.addWidget(self.work_in_progress, 3, 1, 1, 2)
            self.window = QWidget(self)
            self.setCentralWidget(self.window)
            self.window.setLayout(self.layout)
        else:
            pass


    def change_bids_directory(self):
        """
        Update the GUI when the bids database has been modified

        Returns
        -------
        None.

        """
        logging.info("update_bids!")

        bids_dir = str(QFileDialog.getExistingDirectory(self, "Select BIDS Directory", options=QFileDialog.DontUseNativeDialog))
        if os.path.isdir(bids_dir):
            self.bids_dir = bids_dir
            self.bids = BIDSHandler(root_dir=self.bids_dir)
            bids_dir_split = self.bids_dir.split('/')
            self.bids_name = bids_dir_split[len(bids_dir_split)-1]
            self.bids_lab = QLabel(self.bids_name)
            self.bids_lab.setFont(QFont('Calibri', 30))

            self.bids_dir_view = BidsDirView(self)

            self.bids_metadata = BidsMetadata(self)

            self.bids_actions.update_bids(self)

            self.viewer = DefaultViewer(self)

            self.layout.deleteLater()
            self.window.deleteLater()

            self.layout = QGridLayout()
            self.layout.addWidget(self.bids_lab, 0, 1, 1, 2)
            self.layout.addWidget(self.bids_dir_view, 0, 0, 3, 1)
            self.layout.addWidget(self.bids_metadata, 1, 1)
            self.layout.addWidget(self.bids_actions, 1, 2)
            self.layout.addWidget(self.viewer, 2, 1, 1, 2)
            self.layout.addWidget(self.work_in_progress, 3, 1, 1, 2)
            self.window = QWidget(self)
            self.setCentralWidget(self.window)
            self.window.setLayout(self.layout)
        else:
            pass


    def control_bids_quality(self):

        subprocess.Popen(f'docker run --rm -v {self.bids_dir}:/data:ro bids/validator /data --json > bids_validator.json', shell=True).wait()
        with open('bids_validator.json', 'r') as bv:
            bids_validator = json.load(bv)
            bv.close()
        issues = bids_validator.get('issues')
        errors = issues.get('errors')
        warnings = issues.get('warnings')

        self.bids_quality_controler = BIDSQualityControlWindow(self, errors, warnings)
        self.bids_quality_controler.show()


    def update_dataset_description(self):
        """
        Update the authors of the Database

        Returns
        -------
        None.

        """
        if hasattr(self, 'updateDatasetDescription_win'):
            del self.updateDatasetDescription_win
        self.updateDatasetDescription_win = UpdateDatasetDescription(self)
        self.updateDatasetDescription_win.show()


    def add_new_pipelines(self):
        if hasattr(self, 'add_new_pipelines_win'):
            del self.add_new_pipelines_win
        self.add_new_pipelines_win = AddNewPipelinesWindow(self)
        self.add_new_pipelines_win.show()
        
        
    def launch_bids_apps(self):
        pass
        
        
class PreferencesWindow(QDialog):
    """
    """
    
    def __init__(self, parent, memory):
        super().__init__()
        self.setWindowTitle("Preferences")
        self.resize(800, 500)
        self.parent = parent
        self.memory = memory

        # Main layout
        main_layout = QVBoxLayout()

        # Create a scrollable area in case there are many keys
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        # Create one row for each key in the dictionary
        self.key_widgets = {}  # Dictionary to store widgets for easy access
        for key, value in self.memory.items():
            # Create widgets for each key
            row_layout = QHBoxLayout()
            label = QLabel(key)
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(value)
            browse_button = QPushButton("Browse")

            # Store QLineEdit in the dictionary
            self.key_widgets[key] = line_edit

            # Connect the browse button to a file dialog function
            browse_button.clicked.connect(lambda checked, k=key: self.browse_file(k))

            # Add widgets to row layout
            row_layout.addWidget(label)
            row_layout.addWidget(line_edit)
            row_layout.addWidget(browse_button)

            # Add row layout to the main layout
            scroll_layout.addLayout(row_layout)

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)

        # Add scroll area to the main layout
        main_layout.addWidget(scroll_area)

        # Add Apply and Quit buttons at the bottom
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply")
        quit_button = QPushButton("Quit")

        # Connect buttons to their functions
        apply_button.clicked.connect(self.apply_changes)
        quit_button.clicked.connect(self.close)

        button_layout.addWidget(apply_button)
        button_layout.addWidget(quit_button)

        # Add the button layout to the main layout
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def browse_file(self, key):
        # Open a file dialog to select a file
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Application Path", options=QFileDialog.DontUseNativeDialog)
        if file_path:
            # Update the QLineEdit placeholder text with the selected file path
            self.key_widgets[key].setPlaceholderText(file_path)

    def apply_changes(self):
        # Update the data dictionary with values from QLineEdits
        for key, line_edit in self.key_widgets.items():
            text = line_edit.text()
            if text:  # Only update if there is a new text entered
                self.memory[key] = text
            else:
                self.memory[key] = line_edit.placeholderText()
        # Optionally, save the updated data back to the file here
        print("Preferences updated.")
    


# =============================================================================
# Add New Pipelines
# =============================================================================
class AddNewPipelinesWindow(QMainWindow):
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
        self.setMinimumSize(QSize(700,700))

        self.setWindowTitle("Add New Pipeline")
        
        self.parent = parent
        
        self.repos = self.get_github_repositories()
        
        # Create widgets for each repositories
        repos_widget = []
        for repo in self.repos:
            repo_widget = GitHubRepositoryWidget(self, repo)
            repos_widget.append(repo_widget)
        
        layout = QVBoxLayout()
        for repo in repos_widget:
            layout.addWidget(repo)
            
        vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(vertical_spacer)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAutoFillBackground(True)
        scroll_area.setBackgroundRole(QPalette.Base)
        
        scroll_area.setLayout(layout)
        
        self.setCentralWidget(scroll_area)
        
    # def get_github_repositories(self):
    #     url = 'https://github.com/orgs/BMAT-Apps/repositories'
    #     html = requests.get(url)
    #     soup = BeautifulSoup(html.content, 'html5lib')
        
    #     # Find all repositories
    #     repos = soup.find('div', {'class':'org-repos repo-list'})        
    #     list_repos = [item for item in repos.findAll('div', {'class':'flex-auto', 'data-view-component':True})]
        
    #     repos_dic = []
    #     for repo in list_repos:
    #         rep = {}
    #         rep['Name'] = repo.h3.a.text.strip()
    #         rep['href'] = repo.h3.a['href']
    #         rep['desc'] = repo.p.text.strip()
    #         repos_dic.append(rep)
            
    #     return repos_dic
    def get_github_repositories(self):
        url = 'https://api.github.com/orgs/BMAT-Apps/repos'
        response = requests.get(url)
        data = response.json()
        repos_dic = []
        for repo in data:
            rep = {
                'Name': repo['name'],
                'href': repo['html_url'],
                'desc': repo['description'] if repo['description'] else 'No description',
                'stars': repo['stargazers_count'],
                'forks': repo['forks_count'],
                'issues': repo['open_issues_count'],
                'language': repo['language'] if repo['language'] else 'N/A',
                'last_updated': repo['updated_at']
            }
            repos_dic.append(rep)
        return repos_dic
            

# =============================================================================
# Github repository Widget
# =============================================================================
class GitHubRepositoryWidget(QWidget):
    """
    """
    
    def __init__(self, parent, repo):
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
        
        self.repo = repo
        
        self.setMinimumWidth(650)
        
        self.repo_button = QPushButton(repo.get('Name'))
        self.repo_button.setFont(QFont('Calibri', 20))
        self.repo_button.clicked.connect(self.repo_widget)
        
        self.description = QLabel(repo.get('desc'))
        self.description.setFont(QFont('Calibri', 13))
        self.description.setWordWrap(True)
        
        hspacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)  
        
        layout = QVBoxLayout()
        lay = QHBoxLayout()
        lay.addWidget(self.repo_button)
        lay.addItem(hspacer)
        layout.addLayout(lay)
        layout.addWidget(self.description)
        
        self.setLayout(layout)
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QPalette.Background)
        
    def repo_widget(self):
        if hasattr(self, 'repo_widget_win'):
            del self.repo_widget_win
        self.repo_widget_win = RepositoryWidget(self.parent, self.repo)
        self.repo_widget_win.show()
        self.parent.hide()

    
    
# =============================================================================
# RepositoryWidget
# =============================================================================
class RepositoryWidget(QMainWindow):
    """
    """
    
    def __init__(self, parent, repo):
        """
        

        Parameters
        ----------
        parent : TYPE
            DESCRIPTION.
        repo_ref : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        super().__init__()
        self.parent = parent
        self.repo = repo
        
        self.window = QWidget(self)
        
        self.window.setMinimumSize(QSize(1200, 700))
        self.setWindowTitle(self.repo.get('Name'))
        
        self.back_button = QPushButton('Back')
        self.back_button.clicked.connect(self.back)
        
        self.repo_name = QLabel(self.repo.get('Name'))
        self.repo_name.setFont(QFont('Calibri', 30))
        
        self.description = QLabel(self.repo.get('desc'))
        self.description.setFont(QFont('Calibri', 15))
        self.description.setWordWrap(True)
        
        if self.repo.get('Name') not in self.parent.parent.pipelines_name:
            self.pipeline_button = QPushButton('Get Pipeline')
            self.pipeline_button.clicked.connect(self.get_pipeline)
        else:
            self.pipeline_button = QPushButton('Update Pipeline')
            self.pipeline_button.clicked.connect(self.update_pipeline)
        
        hspacer1 = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum) 
        hspacer2 = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum) 
        
        # readme_url = f'https://raw.githubusercontent.com/BIDS-Apps/{self.repo.get("Name")}/main/README.md'
        
        # readme = QTextEdit()
        
        # readme_raw = requests.get(readme_url)
        
        # readme_html = markdown.markdown(readme_raw.text)
        
        # readme.setHtml(readme_html)
        
        url = f'https://github.com/BMAT-Apps/{self.repo.get("Name")}'
        # url = 'https://github.com/ColinVDB/BMAT'
        
        # html = requests.get(url)
        # soup = BeautifulSoup(html.content, 'html5lib')
        
        # # Find all repositories
        # readme_html = soup.find('article', {'class':'markdown-body entry-content container-lg', 'itemprop':'text'})
        # readme = QTextEdit()
        # readme.setHtml(str(readme_html))
        
        web = QWebEngineView()
        web.load(QUrl(url))
        
        layout = QVBoxLayout()
        lay1 = QHBoxLayout()
        lay1.addWidget(self.back_button)
        lay1.addItem(hspacer1)
        lay = QHBoxLayout()
        lay.addWidget(self.repo_name)
        lay.addItem(hspacer2)
        lay.addWidget(self.pipeline_button)
        layout.addLayout(lay1)
        layout.addLayout(lay)
        layout.addWidget(self.description)
        layout.addWidget(web)
        
        self.window.setLayout(layout)
        
        self.setCentralWidget(self.window)
        
        
    def get_pipeline(self):
        self.thread = QThread()
        self.worker = AddPipelineWorker(self.repo)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.in_progress.connect(self.add_update_in_progress)
        self.worker.finished.connect(self.update_pipelines)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
    
    
    def update_pipeline(self):
        self.thread = QThread()
        self.worker = UpdatePipelineWorker(self.repo)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.in_progress.connect(self.add_update_in_progress)
        self.worker.finished.connect(self.update_pipelines)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        
    def update_pipelines(self):
        self.parent.parent.update_pipelines()
    
    
    def back(self):
        self.parent.show()
        self.close()
        self.deleteLater()
        
        
    def add_update_in_progress(self, in_progress):
        if 'Add' in in_progress[0]:
            if in_progress[1]:
                if hasattr(self, 'add_win'):
                    self.add_win.deleteLater()
                    del self.add_win
                self.add_win = AddUpdatePipelineWindow(self, self.repo.get('Name'), 'Add')
                self.add_win.show()
            else:
                if not hasattr(self, 'add_win'):
                    pass
                else:
                    self.add_win.update(in_progress)
            
        elif 'Update' in in_progress[0]:
            if in_progress[1]:
                if hasattr(self, 'add_win'):
                    self.add_win.deleteLater()
                    del self.add_win
                self.add_win = AddUpdatePipelineWindow(self, self.repo.get('Name'), 'Update')
                self.add_win.show()
            else:
                if not hasattr(self, 'add_win'):
                    pass
                else:
                    self.add_win.update(in_progress)
            
        else:
            if not hasattr(self, 'add_win'):
                pass
            else:
                self.add_win.update(in_progress)
                
                
                
# =============================================================================
# AddUpdatePipelineWindow
# =============================================================================
class AddUpdatePipelineWindow(QMainWindow):
    """
    """
    
    def __init__(self, parent, name, check):
        """

        Parameters
        ----------
        parent : TYPE
            DESCRIPTION.
        name : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        super().__init__()
        self.parent = parent
        
        if check == 'Add':
            self.setWindowTitle(f"Add {name}")
        elif check == 'Update':
            self.setWindowTitle(f'Update {name}')
        else:
            self.setWindowTitle('{name} ?')
            
        self.window = QWidget()
        
        self.git_working_gif = QMovie(pjoin(get_executable_path(), 'Pictures', 'roll_load.gif'))
        self.git_working_gif.setScaledSize(QSize(25,25))
        
        self.python_working_gif = QMovie(pjoin(get_executable_path(), 'Pictures', 'roll_load.gif'))
        self.python_working_gif.setScaledSize(QSize(25,25))
        
        self.docker_working_gif = QMovie(pjoin(get_executable_path(), 'Pictures', 'roll_load.gif'))
        self.docker_working_gif.setScaledSize(QSize(25,25))
        
        self.working_gif = QMovie(pjoin(get_executable_path(), 'Pictures', 'roll_load.gif'))
        self.working_gif.setScaledSize(QSize(25,25))
        
        self.check_icon = QPixmap(pjoin(get_executable_path(), 'Pictures', 'check.png'))
        self.check_icon = self.check_icon.scaled(QSize(20,20))
        
        git_lab = QLabel('Git')
        self.git_check = QLabel()
        self.git_check.setMovie(self.git_working_gif)
        
        python_lab = QLabel('Python requirements')
        self.python_check = QLabel()
        self.python_check.setMovie(self.python_working_gif)
        
        docker_lab = QLabel('docker')
        self.docker_check = QLabel()
        self.docker_check.setMovie(self.docker_working_gif)
        
        self.general_check = QLabel()
        self.general_check.setMovie(self.working_gif)
        
        self.working_gif.start()
        
        layout = QGridLayout()
        layout.addWidget(git_lab,0,0,1,1)
        layout.addWidget(self.git_check,0,1,1,1)
        layout.addWidget(python_lab,1,0,1,1)
        layout.addWidget(self.python_check,1,1,1,1)
        layout.addWidget(docker_lab,2,0,1,1)
        layout.addWidget(self.docker_check,2,1,1,1)
        layout.addWidget(self.general_check,3,0,1,2)
        
        self.window.setLayout(layout)
        
        self.setCentralWidget(self.window)
        
        self.center()
        
        
    def update(self, in_progress):
        if 'repo' in in_progress[0]:
            if in_progress[1]:
                self.git_working_gif.start()
            else:
                self.git_working_gif.stop()
                self.git_check.clear()
                self.git_check.setPixmap(self.check_icon)
        elif 'python' in in_progress[0]:
            if in_progress[1]:
                self.python_working_gif.start()
            else:
                self.python_working_gif.stop()
                self.python_check.clear()
                self.python_check.setPixmap(self.check_icon)
        elif 'docker' in in_progress[0]:
            if in_progress[1]:
                self.docker_working_gif.start()
            else:
                self.docker_working_gif.stop()
                self.docker_check.clear()
                self.docker_check.setPixmap(self.check_icon)
        elif 'Add' in in_progress[0] or 'Update' in in_progress[0]:
            if in_progress[1]:
                pass
            else:
                self.working_gif.stop()
                self.general_check.clear()
                self.general_check.setPixmap(self.check_icon)
        else:
            pass
    
    
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
# BIDSQualityControlWindow
# =============================================================================
class BIDSQualityControlWindow(QMainWindow):
    """
    """


    def __init__(self, parent, errors, warnings):
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
        # self.threads_pool = self.parent.threads_pool

        self.setWindowTitle("BIDS Quality Controler")

        self.title = QLabel('BIDS Quality Controler')
        self.title.setFont(QFont('Calibri', 30))

        self.errors = errors

        self.warnings = warnings

        self.info_label = QLabel('Useful Resources')
        self.info_label.setFont(QFont('Calibri', 15))
        self.specification_label = QLabel(f'\tBIDS specification: ' + '<a href="https://bids-specification.readthedocs.io/en/stable/">https://bids-specification.readthedocs.io/en/stable/</a>')
        self.specification_label.setOpenExternalLinks(True)
        self.specification_label.setFont(QFont('Calibri', 15))

        self.init_ui()

        self.center()


    def init_ui(self):
        self.window = QWidget(self)
        self.setCentralWidget(self.window)

        self.errors_label = QLabel(f'Your BIDS directory contains {len(self.errors)} Errors !')
        self.errors_label.setFont(QFont('Calibri', 15))
        self.errors_label.setStyleSheet("color:red")
        self.errors_details_button = QPushButton('Details')
        self.errors_details_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'plus.png')))
        self.errors_details_button.clicked.connect(self.errors_details)

        self.warnings_label = QLabel(f'Your BIDS directory contains {len(self.warnings)} Warnings !')
        self.warnings_label.setFont(QFont('Calibri', 15))
        self.warnings_label.setStyleSheet("color:orange")
        self.warnings_details_button = QPushButton('Details')
        self.warnings_details_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'plus.png')))
        self.warnings_details_button.clicked.connect(self.warnings_details)

        self.layout = QGridLayout()
        self.layout.addWidget(self.title, 0, 0, 1, 2, Qt.AlignCenter)
        self.layout.addWidget(self.errors_label, 1, 0, 1, 1)
        self.layout.addWidget(self.errors_details_button, 1, 1, 1, 1)
        self.layout.addWidget(self.warnings_label, 2, 0, 1, 1)
        self.layout.addWidget(self.warnings_details_button, 2, 1, 1, 1)
        self.layout.addWidget(self.info_label, 3, 0, 1, 2)
        self.layout.addWidget(self.specification_label, 4, 0, 1, 2)

        self.window.setLayout(self.layout)
        self.window.adjustSize()
        self.setCentralWidget(self.window)
        # self.centralWidget.adjustSize()
        self.adjustSize()


    def errors_details(self):

        self.details_errors = QTextEdit()
        self.details_errors.setReadOnly(True)
        self.details_errors.setMinimumHeight(400)

        self.warnings_label = QLabel(f'Your BIDS directory contains {len(self.warnings)} Warnings !')
        self.warnings_label.setFont(QFont('Calibri', 15))
        self.warnings_label.setStyleSheet("color:orange")
        self.warnings_details_button = QPushButton('Details')
        self.warnings_details_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'plus.png')))
        self.warnings_details_button.clicked.connect(self.warnings_details)

        self.minus_errors_button = QPushButton()
        self.minus_errors_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'minus.png')))
        self.minus_errors_button.clicked.connect(self.init_ui)

        for error in self.errors:
            self.details_errors.setFontWeight(QFont.Bold)
            self.details_errors.setTextColor(QColor(255,0,0))
            self.details_errors.insertPlainText(f"{error.get('key')}: \n")
            self.details_errors.setTextColor(QColor(0,0,0))
            self.details_errors.insertPlainText(f'\tReason:\n')
            self.details_errors.setFontWeight(QFont.Normal)
            self.details_errors.insertPlainText(f"\t\t{error.get('reason')}\n")
            self.details_errors.setFontWeight(QFont.Bold)
            self.details_errors.insertPlainText(f'\tFiles:\n')
            self.details_errors.setFontWeight(QFont.Normal)
            for file in error.get('files'):
                self.details_errors.insertPlainText(f"\t\t{file.get('file').get('name')}\n")

        self.layout.deleteLater()
        self.window.deleteLater()

        self.layout = QGridLayout()
        self.layout.addWidget(self.title, 0, 0, 1, 2, Qt.AlignCenter)
        self.layout.addWidget(self.errors_label, 1, 0, 1, 1)
        self.layout.addWidget(self.minus_errors_button, 1, 1, 1, 1)
        self.layout.addWidget(self.details_errors, 2, 0, 1, 2)
        self.layout.addWidget(self.warnings_label, 3, 0, 1, 1)
        self.layout.addWidget(self.warnings_details_button, 3, 1, 1, 1)
        self.layout.addWidget(self.info_label, 4, 0, 1, 2)
        self.layout.addWidget(self.specification_label, 5, 0, 1, 2)

        self.window = QWidget(self)
        self.window.setLayout(self.layout)
        self.window.adjustSize()
        self.setCentralWidget(self.window)
        # self.centralWidget.adjustSize()
        self.adjustSize()


    def warnings_details(self):

        self.details_warnings = QTextEdit()
        self.details_warnings.setReadOnly(True)
        self.details_warnings.setMinimumHeight(400)

        self.errors_label = QLabel(f'Your BIDS directory contains {len(self.errors)} Errors !')
        self.errors_label.setFont(QFont('Calibri', 15))
        self.errors_label.setStyleSheet("color:red")
        self.errors_details_button = QPushButton('Details')
        self.errors_details_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'plus.png')))
        self.errors_details_button.clicked.connect(self.errors_details)

        self.minus_warnings_button = QPushButton()
        self.minus_warnings_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'minus.png')))
        self.minus_warnings_button.clicked.connect(self.init_ui)

        for warning in self.warnings:
            self.details_warnings.setFontWeight(QFont.Bold)
            self.details_warnings.setTextColor(QColor(255,165,0))
            self.details_warnings.insertPlainText(f"{warning.get('key')}: \n")
            self.details_warnings.setTextColor(QColor(0,0,0))
            self.details_warnings.insertPlainText(f'\tReason:\n')
            self.details_warnings.setFontWeight(QFont.Normal)
            self.details_warnings.insertPlainText(f"\t\t{warning.get('reason')}\n")
            self.details_warnings.setFontWeight(QFont.Bold)
            self.details_warnings.insertPlainText(f'\tFiles:\n')
            self.details_warnings.setFontWeight(QFont.Normal)
            for file in warning.get('files'):
                if file.get('file') != None:
                    self.details_warnings.insertPlainText(f"\t\t{file.get('file').get('name')}\n")
                else:
                    self.details_warnings.insertPlainText(f"\t\t{file.get('reason')}\n")

        self.layout.deleteLater()
        self.window.deleteLater()

        self.layout = QGridLayout()
        self.layout.addWidget(self.title, 0, 0, 1, 2, Qt.AlignCenter)
        self.layout.addWidget(self.errors_label, 1, 0, 1, 1)
        self.layout.addWidget(self.errors_details_button, 1, 1, 1, 1)
        self.layout.addWidget(self.warnings_label, 2, 0, 1, 1)
        self.layout.addWidget(self.minus_warnings_button, 2, 1, 1, 1)
        self.layout.addWidget(self.details_warnings, 3, 0, 1, 2)
        self.layout.addWidget(self.info_label, 4, 0, 1, 2)
        self.layout.addWidget(self.specification_label, 5, 0, 1, 2)

        self.window = QWidget(self)
        self.window.setLayout(self.layout)
        self.window.adjustSize()
        self.setCentralWidget(self.window)
        # self.centralWidget.adjustSize()
        self.adjustSize()


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
# Work in Progress
# =============================================================================
class WorkInProgress(QWidget):
    """
    Representation of the BIDS directory
    """


    def __init__(self, parent):
        """
        Create an instance of the Viewer of the BIDS directory

        Parameters
        ----------
        parent : MainWindow
            pointer towards the main window (parent of this widget)

        Returns
        -------
        None.

        """
        super().__init__()
        self.parent = parent
        self.bids = self.parent.bids
        # self.threads_pool = self.parent.threads_pool
        self.setWindowTitle('Work in Progress')
        self.setMinimumSize(700, 50)
        
        self.working_lab = QLabel(self)
        self.working_gif = QMovie(pjoin(get_executable_path(), 'Pictures', 'loading_inf.gif'))
        self.working_gif.setScaledSize(QSize(40,40))
        # self.working_lab.setMovie(self.working_gif)
        # self.working_gif.start()
        
        self.working_details_lab = QLabel(self)
        self.working_details_lab.resize(650, 40)
        self.working_details_lab.setAlignment(Qt.AlignLeft)
        self.working_details_lab.setFont(QFont('Calibri', 10))
        # self.working_details_lab.setText("Work in progress")
        
        self.working_details = []
        
        layout = QHBoxLayout()
        layout.addWidget(self.working_lab)
        layout.addWidget(self.working_details_lab)
        self.setLayout(layout)
    
    @pyqtSlot(tuple)
    def update_work_in_progress(self, in_progress):
        if in_progress[1]:
            self.working_details.append(in_progress[0])
        else:
            self.working_details.remove(in_progress[0])
        # self.update_animation()
        QMetaObject.invokeMethod(self, "update_animation", Qt.QueuedConnection)
    
    
    @pyqtSlot()
    def update_animation(self):
        if not self.working_lab:
            print('working label does not exists')
            return
        
        if self.working_details == []:
            self.working_gif.stop()
            self.working_lab.clear()
            self.working_details_lab.clear()
        else:
            self.working_lab.setMovie(self.working_gif)
            self.working_gif.start()
            self.working_details_lab.setText(('['+''.join(i+',' for i in self.working_details))[:-1]+']')        
 


# =============================================================================
# AddNewBIDSApps
# =============================================================================
class AddNewBidsApps(QWidget):
    """
    Representation of the BIDS directory
    """


    def __init__(self, parent):
        """
        Create an instance of the Viewer of the BIDS directory

        Parameters
        ----------
        parent : MainWindow
            pointer towards the main window (parent of this widget)

        Returns
        -------
        None.

        """
        super().__init__()
        self.parent = parent
        self.bids = self.parent.bids
        # self.threads_pool = self.parent.threads_pool
        self.setWindowTitle('Add New BIDS-Apps')
        
        label = QLabel(self)
        label.setText("test")
        
        button = QPushButton("Add New BIDS-Apps")
        button.clicked.connect(self.add_new_bids_apps)
        
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(button)
        
        self.setLayout(layout)
        self.center()
    
    def add_new_bids_apps(self):
        if hasattr(self, 'add_new_bids_apps_info_win'):
            del self.add_new_bids_apps_info_win
        self.add_new_bids_apps_info_win = AddNewBidsApps_info(self)
        self.add_new_bids_apps_info_win.show()
        
    
    def center(self):
        """
        Used to center the window

        Returns
        -------
        None.

        """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        


# =============================================================================
# AddNewBIDSApps_info
# =============================================================================
class AddNewBidsApps_info(QWidget):
    """
    Representation of the BIDS directory
    """


    def __init__(self, parent):
        """
        Create an instance of the Viewer of the BIDS directory

        Parameters
        ----------
        parent : MainWindow
            pointer towards the main window (parent of this widget)

        Returns
        -------
        None.

        """
        super().__init__()
        self.parent = parent
        self.bids = self.parent.bids
        # self.threads_pool = self.parent.threads_pool
        self.setWindowTitle('Add New BIDS-Apps')
        self.setMinimumSize(700, 700)
        
        
        self.center()
        
    def center(self):
        """
        Used to center the window

        Returns
        -------
        None.

        """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        



# =============================================================================
# BidsDirView
# =============================================================================
class BidsDirView(QWidget):
    """
    Representation of the BIDS directory
    """


    def __init__(self, parent):
        """
        Create an instance of the Viewer of the BIDS directory

        Parameters
        ----------
        parent : MainWindow
            pointer towards the main window (parent of this widget)

        Returns
        -------
        None.

        """
        super().__init__()
        self.parent = parent
        self.bids = self.parent.bids
        # self.threads_pool = self.parent.threads_pool
        dir_path = self.parent.bids_dir
        self.setWindowTitle('File System Viewer')
        self.setMinimumSize(250, 700)

        self.model = QFileSystemModel()
        self.model.setRootPath(dir_path)
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(dir_path))
        self.tree.setColumnWidth(0,250)
        self.tree.setAlternatingRowColors(True)
        self.tree.doubleClicked.connect(self.treeMedia_doubleClicked)
        self.tree.clicked.connect(self.treeMedia_clicked)
        self.tree.setDragEnabled(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.openMenu)
        self.threads = []

        self.single_click = True

        self.itksnap = None

        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)


    def update_dir(self):
        """
        Update the directory viewer

        Returns
        -------
        None.

        """
        self.model = QFileSystemModel()
        self.model.setRootPath(self.parent.bids_dir)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.parent.bids_dir))


    def treeMedia_doubleClicked(self, index):
        """
        Action to be performed when an item is double clicked

        Parameters
        ----------
        index : QIndex
            index of the item that has been double clicked

        Returns
        -------
        None.

        """
        # item = self.tree.selectedIndexes()[0]
        # item_path = item.model().filePath(index)
        # if os.path.isfile(item_path):
        #     logging.info(f"[INFO] Opening {item_path}")
        #     if '.nii' in item_path:
        #         self.itksnap = self.parent.memory.get('itksnap')
        #         if self.itksnap == None:
        #             logging.info(f'No application selected open MRI \n \t Please select itksnap path')
        #         else:
        #             print(self.itksnap)
        #             self.threads.append(QThread())
        #             self.operation = SubprocessWorker(f'{self.itksnap} -g {item_path}')
        #             self.operation.moveToThread(self.threads[-1])
        #             self.threads[-1].started.connect(self.operation.run)
        #             self.operation.finished.connect(self.threads[-1].quit)
        #             self.operation.finished.connect(self.operation.deleteLater)
        #             self.threads[-1].finished.connect(self.threads[-1].deleteLater)
        #             self.threads[-1].start()
        #     else:
        #         if self.parent.system == 'Linux':
        #             self.threads.append(QThread())
        #             self.operation = SubprocessWorker(f'xdg-open {item_path}')
        #             self.operation.moveToThread(self.threads[-1])
        #             self.threads[-1].started.connect(self.operation.run)
        #             self.operation.finished.connect(self.threads[-1].quit)
        #             self.operation.finished.connect(self.operation.deleteLater)
        #             self.threads[-1].finished.connect(self.threads[-1].deleteLater)
        #             self.threads[-1].start()
        #         elif self.parent.system == 'Darwin':
        #             self.threads.append(QThread())
        #             self.operation = SubprocessWorker(f'open {item_path}')
        #             self.operation.moveToThread(self.threads[-1])
        #             self.threads[-1].started.connect(self.operation.run)
        #             self.operation.finished.connect(self.threads[-1].quit)
        #             self.operation.finished.connect(self.operation.deleteLater)
        #             self.threads[-1].finished.connect(self.threads[-1].deleteLater)
        #             self.threads[-1].start()
        #         elif self.parent.system == 'Windows':
        #             self.threads.append(QThread())
        #             self.operation = SubprocessWorker(f'start {item_path}')
        #             self.operation.moveToThread(self.threads[-1])
        #             self.threads[-1].started.connect(self.operation.run)
        #             self.operation.finished.connect(self.threads[-1].quit)
        #             self.operation.finished.connect(self.operation.deleteLater)
        #             self.threads[-1].finished.connect(self.threads[-1].deleteLater)
        #             self.threads[-1].start()
        #         else:
        #             logging.warning('The program does not recognize the OS')
        # else:
        #     pass
        item = self.tree.selectedIndexes()[0]
        item_path = item.model().filePath(index)
        if os.path.isdir(pjoin(item_path)):
            return
        if any(['.csv' in item_path, '.tsv' in item_path, '.xlsx' in item_path]):
            if 'participants.tsv' in item_path:
                print('participants.tsv')
                self.parent.updateViewer('participants_tsv', file=item_path)
            else:
                self.parent.updateViewer('table', file=item_path)
        elif any(['.nii' in item_path, '.nii.gz' in item_path]):
            self.itksnap = self.parent.memory.get('itksnap')
            if self.itksnap == None:
                self.itksnap = QFileDialog.getOpenFileName(self, "Select the path to itksnap", options=QFileDialog.DontUseNativeDialog)[0]
                if self.itksnap != None and self.itksnap != '':
                    self.threads.append(QThread())
                    self.operation = SubprocessWorker(f'"{self.itksnap}" -g {item_path}')
                    self.operation.moveToThread(self.threads[-1])
                    self.threads[-1].started.connect(self.operation.run)
                    self.operation.finished.connect(self.threads[-1].quit)
                    self.operation.finished.connect(self.operation.deleteLater)
                    self.threads[-1].finished.connect(self.threads[-1].deleteLater)
                    self.threads[-1].start()
                    self.parent.memory['itksnap'] = self.itksnap
                else:
                    logging.info(f'No application selected open MRI \n \t Please select itksnap path')
            else:
                self.threads.append(QThread())
                self.operation = SubprocessWorker(f'"{self.itksnap}" -g {item_path}')
                self.operation.moveToThread(self.threads[-1])
                self.threads[-1].started.connect(self.operation.run)
                self.operation.finished.connect(self.threads[-1].quit)
                self.operation.finished.connect(self.operation.deleteLater)
                self.threads[-1].finished.connect(self.threads[-1].deleteLater)
                self.threads[-1].start()
        else:
            self.parent.updateViewer('text', file=item_path)

        self.single_click = False


    def treeMedia_clicked(self, index):
        if self.single_click:
            item = self.tree.selectedIndexes()[0]
            item_path = item.model().filePath(index)
            if os.path.isdir(pjoin(item_path)):
                return
            if any(['.nii' in item_path, '.nii.gz' in item_path]):
                self.parent.updateViewer('nifti', file=item_path)
            else:
                self.parent.updateViewer('default', file=item_path)
        else:
            self.single_click = True


    def openMenu(self, position):
        """
        Open a drop down menu when right clicking on an item

        Parameters
        ----------
        position : a position
            The position of the mouse

        Returns
        -------
        None.

        """
        menu = QMenu()
        openWith = menu.addAction('Open with')
        # openAdd = 'None'
        # openSeg = 'None'
        index = self.tree.indexAt(position)
        item = self.tree.selectedIndexes()[0]
        item_path = item.model().filePath(index)
        if '.nii' in item_path:
            if self.itksnap == None:
                self.itksnap = self.parent.memory.get('itksnap')
            # if self.itksnap != None:
            #     openAdd = menu.addAction('Open as additional image')
            #     openSeg = menu.addAction('Open as segmentation')
        action = menu.exec_(self.tree.viewport().mapToGlobal(position))

        if action == openWith:
            logging.debug('Open With')
            self.itksnap = QFileDialog.getOpenFileName(self, "Select the path to itksnap", options=QFileDialog.DontUseNativeDialog)[0]
            if self.itksnap != None and self.itksnap != '':
                self.threads.append(QThread())
                self.operation = SubprocessWorker(f'"{self.itksnap}" -g {item_path}')
                self.operation.moveToThread(self.threads[-1])
                self.threads[-1].started.connect(self.operation.run)
                self.operation.finished.connect(self.threads[-1].quit)
                self.operation.finished.connect(self.operation.deleteLater)
                self.threads[-1].finished.connect(self.threads[-1].deleteLater)
                self.threads[-1].start()
                self.parent.memory['itksnap'] = self.itksnap
            else:
                logging.info(f'No application selected open MRI \n \t Please select itksnap path')

        # if action == openAdd:
        #     logging.debug('Open as additional image')
        #     self.threads.append(QThread())
        #     self.operation = SubprocessWorker(f'itksnap -o {item_path}')
        #     self.operation.moveToThread(self.threads[-1])
        #     self.threads[-1].started.connect(self.operation.run)
        #     self.operation.finished.connect(self.threads[-1].quit)
        #     self.operation.finished.connect(self.operation.deleteLater)
        #     self.threads[-1].finished.connect(self.threads[-1].deleteLater)
        #     self.threads[-1].start()

        # if action == openSeg:
        #     self.threads.append(QThread())
        #     self.operation = SubprocessWorker(f'itksnap -s {item_path}')
        #     self.operation.moveToThread(self.threads[-1])
        #     self.threads[-1].started.connect(self.operation.run)
        #     self.operation.finished.connect(self.threads[-1].quit)
        #     self.operation.finished.connect(self.operation.deleteLater)
        #     self.threads[-1].finished.connect(self.threads[-1].deleteLater)
        #     self.threads[-1].start()



# =============================================================================
# BidsMetaData
# =============================================================================
class BidsMetadata(QWidget):
    """
    Widget containing all meta data about the Bids Database
    """


    def __init__(self, parent):
        """
        Create an instance of the BidsMetadat Widget

        Parameters
        ----------
        parent : MainWindow
            pointer towards the MainWindow (parent of this widget)

        Returns
        -------
        None.

        """
        super().__init__()
        self.parent = parent
        self.bids = self.parent.bids
        self.number_of_subjects = QLabel(f"Number of subjects: {self.bids.number_of_subjects}")
        self.number_of_subjects.setFont(QFont('Calibri', 15))

        layout = QVBoxLayout()
        layout.addWidget(self.number_of_subjects)

        dataset_description = self.bids.get_dataset_description()
        bids_version = dataset_description.get('BIDSVersion')
        authors = dataset_description.get('Authors')

        self.bids_version = QLabel(f"BIDSVersion: {bids_version}")
        self.bids_version.setFont(QFont('Calibri', 12))
        layout.addWidget(self.bids_version)

        authors_lab = f"Authors: "
        authors = authors if authors != None else []
        if len(authors) <= 3:
            for author in authors:
                if author == authors[-1]:
                    authors_lab = authors_lab + author
                else:
                    authors_lab = authors_lab + f'{author}\n            '
        else:
            authors_lab = authors_lab + authors[0] + ' et al.'
        self.authors = QLabel(authors_lab)
        self.authors.setFont(QFont('Calibri', 12))
        layout.addWidget(self.authors)

        self.setLayout(layout)


    def update_metadata(self):
        """
        Update the metadata information

        Returns
        -------
        None.

        """
        self.bids = self.parent.bids
        self.bids.update_number_of_subjects()
        self.number_of_subjects.setText(f"Number of subjects: {self.bids.number_of_subjects}")
        dataset_description = self.bids.get_dataset_description()
        bids_version = dataset_description.get('BIDSVersion')
        authors = dataset_description.get('Authors')
        authors_lab = "Authors: "
        authors = authors if authors != None else []
        if len(authors) <= 3:
            for author in authors:
                if author == authors[-1]:
                    authors_lab = authors_lab + author
                else:
                    authors_lab = authors_lab + f'{author}\n         '
        else:
            authors_lab = authors_lab + authors[0] + ' et al.'
        self.bids_version.setText(f"BIDSVersion: {bids_version}")
        self.authors.setText(authors_lab)
        
        name = dataset_description.get('Name')
        self.parent.bids_lab.setText(name)



# =============================================================================
# BidsActions
# =============================================================================
class BidsActions(QWidget):
    """
    Widget containing all the possible actions that can be performed on the
    Bids Database
    """


    def __init__(self, parent):
        """
        Create an instance of the BidsAction Widget

        Parameters
        ----------
        parent : MainWindow
            Pointer towards the Main Window (parent of this widget)

        Returns
        -------
        None.

        """
        super().__init__()
        self.parent = parent
        self.bids = self.parent.bids
        # self.threads_pool = self.parent.threads_pool

        # self.change_bids_dir_button = QPushButton("Change BIDS Directory")
        # self.change_bids_dir_button.clicked.connect(self.change_bids_dir)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add)

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove)

        # self.rename_sub_button = QPushButton("Rename subject")
        # self.rename_sub_button.clicked.connect(self.rename_sub)

        # self.rename_ses_button = QPushButton("Rename session")
        # self.rename_ses_button.clicked.connect(self.rename_ses)

        # self.rename_seq_button = QPushButton("Rename sequence")
        # self.rename_seq_button.clicked.connect(self.rename_seq)

        # self.update_authors_button = QPushButton("Update authors")
        # self.update_authors_button.clicked.connect(self.update_authors)

        self.rename_button = QPushButton("Rename subject/session/sequence")
        self.rename_button.clicked.connect(self.rename)

        layout = QGridLayout()
        # layout.addWidget(self.change_bids_dir_button, 0, 0, 1, 2)
        layout.addWidget(self.add_button, 0, 0, 1, 1)
        layout.addWidget(self.remove_button, 0, 1, 1, 1)
        # layout.addWidget(self.rename_sub_button, 2, 0, 1, 1)
        # layout.addWidget(self.rename_ses_button, 2, 1, 1, 1)
        # layout.addWidget(self.rename_seq_button, 3, 0, 1, 1)
        # layout.addWidget(self.update_authors_button, 3, 1, 1, 1)
        layout.addWidget(self.rename_button, 1, 0, 1, 2)

        self.setLayout(layout)


    def change_bids_dir(self):
        """
        Change bids directory

        Returns
        -------
        None.

        """
        logging.info("change_bids_dir")
        self.parent.update_bids()


    def add(self):
        """
        Add a new subject/session

        Returns
        -------
        None.

        """
        class ActionDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                # self.parent = parent
                # self.bids = self.parent.bids
                self.initUI()
                
            def initUI(self):
                self.setWindowTitle('Choose Action')
                label = QLabel('Do you want to perform the conversion locally or the SSS server?', self)
                
                local_button = QPushButton('Locally', self)
                local_button.clicked.connect(self.performLocally)
                
                remote_button = QPushButton('SSS Server', self)
                remote_button.clicked.connect(self.performOnRemote)
                
                layout = QVBoxLayout()
                layout.addWidget(label)
                layout_button = QHBoxLayout()
                layout_button.addWidget(local_button)
                layout_button.addWidget(remote_button)
                layout.addLayout(layout_button)
                
                self.setLayout(layout)
                
            def performLocally(self):
                print('Performing action locally...')
                self.result = 'locally'
                self.accept()
                
                # logging.info("add")
                # if hasattr(self, 'add_win'):
                #     del self.add_win
                # print('test')
                # self.add_win = AddWindow(self.parent)
                # print('creation of the add window')
                # if not self.parent.parent.dcm2niix_path:
                #     print('no dcm2niix path')
                #     # ajouter une fenetre
                #     path = QFileDialog.getOpenFileName(self, "Select 'dcm2niix.exe' path", options=QFileDialog.DontUseNativeDialog)[0]
                #     self.parent.parent.dcm2niix_path = path
                #     # self.parent.memory['dcm2niix_path'] = path
                #     self.bids.setDicom2niixPath(self.parent.parent.dcm2niix_path)
                # self.add_win.show()
                # print('show window')
                # self.close()
                # print('hide qfiledialog')
                
            def performOnRemote(self):
                print('Performing action on remote server...')
                self.result = 'remote'
                self.accept()
                
                # logging.info("add")
                # if hasattr(self, 'add_win_server'):
                #     del self.add_win_server
                # self.add_win_server = AddServerWindow(self.parent)
                # self.add_win_server.show()
                # self.hide()
        
        # check if server info completed in json
        server_info = get_server_info()
        if server_info == None:
            print('server_info == None')
            if hasattr(self, 'add_win'):
                del self.add_win
            self.add_win = AddWindow(self)
            if not self.parent.memory.get('dcm2niix_path'):
                print('no dcm2niix path')
                # ajouter une fenetre
                path = QFileDialog.getOpenFileName(self, "Select 'dcm2niix.exe' path", options=QFileDialog.DontUseNativeDialog)[0]
                if path != None and path != '' and pexists(path):
                    self.parent.memory['dcm2niix_path'] = path
                    # self.parent.memory['dcm2niix_path'] = path
                    self.bids.setDicom2niixPath(self.parent.memory.get('dcm2niix_path'))
                    self.parent.memory['dcm2niix_path'] = path
            self.add_win.show()
            print('show window')
        elif server_info.get('server') == None or server_info.get('server') == "":
            print('server_info.get(server) == None')
            if hasattr(self, 'add_win'):
                del self.add_win
            self.add_win = AddWindow(self)
            if not self.parent.memory.get('dcm2niix_path'):
                print('no dcm2niix path')
                # ajouter une fenetre
                path = QFileDialog.getOpenFileName(self, "Select 'dcm2niix.exe' path", options=QFileDialog.DontUseNativeDialog)[0]
                if path != None and path != '' and pexists(path):
                    self.parent.memory['dcm2niix_path'] = path
                    # self.parent.memory['dcm2niix_path'] = path
                    self.bids.setDicom2niixPath(self.parent.memory.get('dcm2niix_path'))
                    self.parent.memory['dcm2niix_path'] = path
            self.add_win.show()
            print('show window')
        elif server_info.get('server').get('host') == None or server_info.get('server').get('host') == "":
            print('server_info.get(server).get(host) == None')
            if hasattr(self, 'add_win'):
                del self.add_win
            self.add_win = AddWindow(self)
            if not self.parent.memory.get('dcm2niix_path'):
                print('no dcm2niix path')
                # ajouter une fenetre
                path = QFileDialog.getOpenFileName(self, "Select 'dcm2niix.exe' path", options=QFileDialog.DontUseNativeDialog)[0]
                if path != None and path != '' and pexists(path):
                    self.parent.memory['dcm2niix_path'] = path
                    # self.parent.memory['dcm2niix_path'] = path
                    self.bids.setDicom2niixPath(self.parent.memory.get('dcm2niix_path'))
                    self.parent.memory['dcm2niix_path'] = path
            self.add_win.show()
            print('show window')
        else:        
            dialog = ActionDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                result = dialog.result
                print(result)
                
                if result == 'locally':
                    if hasattr(self, 'add_win'):
                        del self.add_win
                    self.add_win = AddWindow(self)
                    if not self.parent.memory.get('dcm2niix_path'):
                        print('no dcm2niix path')
                        # ajouter une fenetre
                        path = QFileDialog.getOpenFileName(self, "Select 'dcm2niix.exe' path", options=QFileDialog.DontUseNativeDialog)[0]
                        if path != None and path != '' and pexists(path):
                            self.parent.memory['dcm2niix_path'] = path
                            # self.parent.memory['dcm2niix_path'] = path
                            self.bids.setDicom2niixPath(self.parent.memory.get('dcm2niix_path'))
                            self.parent.memory['dcm2niix_path'] = path
                    self.add_win.show()
                    print('show window')
                    # self.hide()
                    print('hide qdialog')
                
                elif result == 'remote':
                    print("add")
                    if hasattr(self, 'add_win_server'):
                        del self.add_win_server
                    self.add_win_server = AddServerWindow(self.parent)
                    self.add_win_server.show()
                    # self.hide()


    def remove(self):
        """
        Remove subject/session

        Returns
        -------
        None.

        """
        logging.info("remove")
        if hasattr(self, 'rm_win'):
            del self.rm_win
        self.rm_win = RemoveWindow(self)
        self.rm_win.show()


    def rename_sub(self):
        """
        Rename subject

        Returns
        -------
        None.

        """
        logging.info("rename_sub")
        if hasattr(self, 'renameSub_win'):
            del self.renameSub_win
        self.renameSub_win = RenameSubject(self)
        self.renameSub_win.show()


    def rename(self):
        """
        Rename subject

        Returns
        -------
        None.

        """
        logging.info("rename")
        if hasattr(self, 'rename_win'):
            del self.rename_win
        self.rename_win = Rename(self)
        self.rename_win.show()


    def rename_ses(self):
        """
        Rename session

        Returns
        -------
        None.

        """
        logging.info("rename_ses")
        if hasattr(self, 'renameSes_win'):
            del self.renameSes_win
        self.renameSes_win = RenameSession(self)
        self.renameSes_win.show()


    def update_bids(self, parent):
        """
        Update Bids directory

        Parameters
        ----------
        parent : MainWindow
            Pointer towards the Main Window (parent to this widget)

        Returns
        -------
        None.

        """
        self.parent = parent
        self.bids = self.parent.bids


    def rename_seq(self):
        """
        Rename a sequence

        Returns
        -------
        None.

        """
        logging.info("rename_seq")
        if hasattr(self, 'renameSeq_win'):
            del self.renameSeq_win
        self.renameSeq_win = RenameSequence(self)
        self.renameSeq_win.show()


    def update_authors(self):
        """
        Update the authors of the Database

        Returns
        -------
        None.

        """
        logging.info("update_authors")
        if hasattr(self, 'updateDatasetDescription_win'):
            del self.updateDatasetDescription_win
        self.updateDatasetDescription_win = UpdateDatasetDescription(self)
        self.updateDatasetDescription_win.show()


    def setEnabledButtons(self, enabled):
        """
        Enable or Disable all the buttons to avoid concurrent actions on the
        database

        Parameters
        ----------
        enabled : boolean
            True to enable and False to disable the buttons

        Returns
        -------
        None.

        """
        self.change_bids_dir_button.setEnabled(enabled)
        self.add_button.setEnabled(enabled)
        self.remove_button.setEnabled(enabled)
        self.rename_sub_button.setEnabled(enabled)
        self.rename_ses_button.setEnabled(enabled)
        self.rename_seq_button.setEnabled(enabled)
        self.update_authors_button.setEnabled(enabled)



# =============================================================================
# RemoveWindow
# =============================================================================
class RemoveWindow(QMainWindow):
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
        # self.threads_pool = self.parent.threads_pool

        self.setWindowTitle("Remove subject or session")
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.center()

        self.label = QLabel("Select subject or session to remove")
        self.label.setAlignment(Qt.AlignHCenter)
        self.subject = QLineEdit(self)
        self.subject.setPlaceholderText('Subject number')
        self.session = QLineEdit(self)
        self.session.setPlaceholderText('Session number')

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove)

        layout = QGridLayout()
        layout.addWidget(self.label, 0, 0, 1, 2)
        layout.addWidget(self.subject, 1, 0, 1, 1)
        layout.addWidget(self.session, 1, 1, 1, 1)
        layout.addWidget(self.remove_button, 2, 0, 1, 2)

        self.window.setLayout(layout)


    def remove(self):
        """


        Returns
        -------
        None.

        """
        subject = self.subject.text()
        session = self.session.text()
        buttonReply = QMessageBox.question(self, 'Remove subject and/or session', "Do you want to delete the raw dicoms?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            logging.info(f"Removing sub-{subject} ses-{session}")
            if subject != "":
                if session != "":
                    self.parent.setEnabled(False)
                    self.thread = QThread()
                    self.operation = OperationWorker(self.bids.delete_session, args=[subject, session], kwargs={'delete_sourcedata':True})
                    self.operation.moveToThread(self.thread)
                    self.thread.started.connect(self.operation.run)
                    self.operation.in_progress.connect(self.is_in_progress)
                    self.operation.finished.connect(self.thread.quit)
                    self.operation.finished.connect(self.operation.deleteLater)
                    self.thread.finished.connect(self.thread.deleteLater)
                    self.thread.start()
                    self.thread.finished.connect(
                        lambda: self.parent.setEnabled(True)
                    )


                else:
                    self.parent.setEnabled(False)
                    self.thread = QThread()
                    self.operation = OperationWorker(self.bids.delete_subject, args=[subject], kwargs={'delete_sourcedata':True})
                    self.operation.moveToThread(self.thread)
                    self.thread.started.connect(self.operation.run)
                    self.operation.in_progress.connect(self.is_in_progress)
                    self.operation.finished.connect(self.thread.quit)
                    self.operation.finished.connect(self.operation.deleteLater)
                    self.thread.finished.connect(self.thread.deleteLater)
                    # self.operation.logHandler.log.signal.connect(self.write_log)
                    self.thread.start()
                    self.thread.finished.connect(
                        lambda: self.parent.setEnabled(True)
                    )
        else:
            logging.info(f"Removing sub-{subject} ses-{session} while keeping the dicoms")
            if subject != "":
                if session != "":
                    self.parent.setEnabled(False)
                    self.thread = QThread()
                    self.operation = OperationWorker(self.bids.delete_session, args=[subject, session])
                    self.operation.moveToThread(self.thread)
                    self.thread.started.connect(self.operation.run)
                    self.operation.in_progress.connect(self.is_in_progress)
                    self.operation.finished.connect(self.thread.quit)
                    self.operation.finished.connect(self.operation.deleteLater)
                    self.thread.finished.connect(self.thread.deleteLater)
                    self.thread.start()
                    self.thread.finished.connect(
                        lambda: self.parent.setEnabled(True)
                    )
                else:
                    self.parent.setEnabled(False)
                    self.thread = QThread()
                    self.operation = OperationWorker(self.bids.delete_subject, args=[subject])
                    self.operation.moveToThread(self.thread)
                    self.thread.started.connect(self.operation.run)
                    self.operation.in_progress.connect(self.is_in_progress)
                    self.operation.finished.connect(self.thread.quit)
                    self.operation.finished.connect(self.operation.deleteLater)
                    self.thread.finished.connect(self.thread.deleteLater)
                    self.thread.start()
                    self.thread.finished.connect(
                        lambda: self.parent.setEnabled(True)
                    )

        self.hide()
        
    def is_in_progress(self, in_progress):
        self.parent.parent.work_in_progress.update_work_in_progress(in_progress)


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
# AddWindow
# =============================================================================
class AddWindow(QMainWindow):
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
        # self.threads_pool = self.parent.threads_pool

        self.setWindowTitle("Add subject or session")
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.center()

        self.list_to_add = []

        self.label = QLabel("Select DICOM folders to add to BIDS directory")
        self.label.setAlignment(Qt.AlignHCenter)

        self.add_folder_button = QPushButton("Add DICOM Folder")
        self.add_folder_button.clicked.connect(self.add_folder)
        self.add_files_button = QPushButton("Add DICOM zip Files")
        self.add_files_button.clicked.connect(self.add_files)
        self.list_view = QTableWidget()
        self.list_view.setMinimumSize(800,200)
        self.list_view.setColumnCount(3)
        self.list_view.setColumnWidth(0, 600)
        self.list_view.setColumnWidth(1, 100)
        self.list_view.setColumnWidth(2, 100)
        self.list_view.setAlternatingRowColors(True)
        self.list_view.setHorizontalHeaderLabels(["path", "subject", "session"])
        self.add_button = QPushButton("Add to BIDS directory")
        self.add_button.clicked.connect(self.add)

        layout = QGridLayout()
        layout.addWidget(self.label, 0, 0, 1, 2)
        layout.addWidget(self.add_folder_button, 1, 0, 1, 1)
        layout.addWidget(self.add_files_button, 1, 1, 1, 1)
        layout.addWidget(self.list_view, 2, 0, 1, 2)
        layout.addWidget(self.add_button, 3, 0, 1, 2)

        self.window.setLayout(layout)


    def add_folder(self):
        """


        Returns
        -------
        None.

        """
        dicom_folder = str(QFileDialog.getExistingDirectory(self, "Select DICOM folder", options=QFileDialog.DontUseNativeDialog))
        rowPosition = len(self.list_to_add)
        self.list_view.insertRow(rowPosition)
        self.list_view.setItem(rowPosition , 0, QTableWidgetItem(dicom_folder))
        self.list_view.setItem(rowPosition , 1, QTableWidgetItem(None))
        self.list_view.setItem(rowPosition , 2, QTableWidgetItem(None))


    def add_files(self):
        """


        Returns
        -------
        None.

        """
        dicom_folder = QFileDialog.getOpenFileName(self, 'Select DICOM zip file', options=QFileDialog.DontUseNativeDialog)[0]
        rowPosition = len(self.list_to_add)
        self.list_view.insertRow(rowPosition)
        self.list_view.setItem(rowPosition , 0, QTableWidgetItem(dicom_folder))
        self.list_view.setItem(rowPosition , 1, QTableWidgetItem(None))
        self.list_view.setItem(rowPosition , 2, QTableWidgetItem(None))


    def add(self):
        """


        Returns
        -------
        None.

        """
        #get items
        for i in range(self.list_view.rowCount()):
            self.list_to_add.append((self.list_view.item(i,0).text(), self.list_view.item(i,1).text() if self.list_view.item(i,1).text() != '' else None, self.list_view.item(i,2).text() if self.list_view.item(i,2).text() != '' else None))

        self.parent.setEnabled(False)
        self.thread = QThread()
        self.worker = AddWorker(self.bids, self.list_to_add)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.in_progress.connect(self.is_in_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.cleanup_thread)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: self.end_add())
        self.thread.start()

        self.hide()
        
    
    def is_in_progress(self, in_progress):
        self.parent.parent.work_in_progress.update_work_in_progress(in_progress)
        
    @pyqtSlot()
    def cleanup_thread(self):
        # Wait for the thread to finish
        self.thread.wait()

    def closeEvent(self, event):
        # Ensure the thread is properly shut down before the widget is closed
        if hasattr(self, 'thread'):
            print('self has thread attr')
            try:
                self.thread.quit()
                self.thread.wait()
            except AttributeError:
                print('[Warning] attribute error')
        event.accept()  # Accept the close event
    

    def end_add(self):
        """


        Returns
        -------
        None.

        """
        self.parent.parent.bids_metadata.update_metadata()
        logging.info(f'All done.')
        self.parent.setEnabled(True)


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
        
    
        
class AddServerWindow(QMainWindow):
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

        self.setWindowTitle("Add MRI session on SSS cluster")
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.center()
        
        # get job_info
        path = get_executable_path()
        if not pexists(pjoin(path, 'dcm2bids_sss.json')):
            print('[ERROR] dcm2bids_sss.json file not found')
        
        self.job_json = None
        with open(pjoin(path, 'dcm2bids_sss.json'), 'r') as f:
            self.job_json = json.load(f)
        
        self.tabs = QTabWidget(self)
        
        self.main_tab = AddServerTab(self)
        self.job_tab = JobTab(self, self.job_json.get("slurm_infos"))
        
        self.tabs.addTab(self.main_tab, "Main")
        self.tabs.addTab(self.job_tab, "Slurm Job")
        
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)

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
# AddWindow
# =============================================================================
class AddServerTab(QWidget):
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
        # self.threads_pool = self.parent.threads_pool
        
        self.job_json = self.parent.job_json

        self.list_to_add = []

        self.label = QLabel("Select DICOM zip file to add to BIDS directory")
        self.label.setAlignment(Qt.AlignHCenter)

        # self.add_folder_button = QPushButton("Add DICOM Folder")
        # self.add_folder_button.clicked.connect(self.add_folder)
        self.checkbox = QCheckBox('ISO format', self)
        self.checkbox.stateChanged.connect(self.on_state_changed)
        self.iso = False
        self.add_files_button = QPushButton("Add DICOM zip Files")
        self.add_files_button.clicked.connect(self.add_files)
        self.list_view = QTableWidget()
        self.list_view.setMinimumSize(800,200)
        self.list_view.setColumnCount(3)
        self.list_view.setColumnWidth(0, 600)
        self.list_view.setColumnWidth(1, 100)
        self.list_view.setColumnWidth(2, 100)
        self.list_view.setAlternatingRowColors(True)
        self.list_view.setHorizontalHeaderLabels(["path", "subject", "session"])
        self.add_button = QPushButton("Add to BIDS directory")
        self.add_button.clicked.connect(self.add)

        layout = QGridLayout()
        layout.addWidget(self.label, 0, 0, 1, 2)
        layout.addWidget(self.add_files_button, 1, 0, 1, 1)
        layout.addWidget(self.checkbox, 1, 1, 1, 1, Qt.AlignRight)
        layout.addWidget(self.list_view, 2, 0, 1, 2)
        layout.addWidget(self.add_button, 3, 0, 1, 2)

        self.setLayout(layout)


    def on_state_changed(self, state):
        if state == Qt.Checked:
            self.iso = True
        else:
            self.iso = False


    def add_files(self):
        """


        Returns
        -------
        None.

        """
        dicom_folder = QFileDialog.getOpenFileName(self, 'Select DICOM zip file', options=QFileDialog.DontUseNativeDialog)[0]
        if dicom_folder == None or dicom_folder == '':
            return
        rowPosition = len(self.list_to_add)
        self.list_view.insertRow(rowPosition)
        self.list_view.setItem(rowPosition , 0, QTableWidgetItem(dicom_folder))
        self.list_view.setItem(rowPosition , 1, QTableWidgetItem(None))
        self.list_view.setItem(rowPosition , 2, QTableWidgetItem(None))


    def add(self):
        """


        Returns
        -------
        None.

        """
        self.job_json["slurm_infos"] = self.parent.job_tab.get_slurm_job_info()
        
        def getPassword():
            password, ok = QInputDialog.getText(self, "SSH Key Passphrase", "Unlocking SSH key with passphrase?", 
                                    QLineEdit.Password)
            passphrase = None
            if ok and password:
                passphrase = password
            return passphrase
        
        passphrase = getPassword()
        
        #get items
        for i in range(self.list_view.rowCount()):
            self.list_to_add.append((self.list_view.item(i,0).text(), self.list_view.item(i,1).text() if self.list_view.item(i,1).text() != '' else None, self.list_view.item(i,2).text() if self.list_view.item(i,2).text() != '' else None))

        # self.parent.setEnabled(False)
        # self.thread = QThread()
        # self.worker = AddServerWorker(self.bids, self.list_to_add, self.iso, self.job_json, passphrase=passphrase)
        # self.worker.moveToThread(self.thread)
        # self.thread.started.connect(self.worker.run)
        # self.worker.in_progress.connect(self.is_in_progress)
        # self.worker.error.connect(self.error_handler)
        # self.worker.jobs_submitted.connect(self.submitted_jobs)
        # self.worker.finished.connect(self.thread.quit)
        # self.worker.finished.connect(self.worker.deleteLater)
        # self.thread.finished.connect(self.thread.deleteLater)
        # self.thread.finished.connect(lambda: self.end_add())
        # self.thread.start()
        
        # Do the job here and not in a thread 
        self.is_in_progress(('AddServer', True))
        jobs_id = []
            
        for item in self.list_to_add:

            dicom = item[0]

            if not ".zip" in dicom:
                print ('Not a zip file')
                return 
    
            dicom_file = dicom
            sub = item[1]
            ses = item[2]
                
            try:
                args = [dicom_file]
                if self.iso:
                    args.append('-iso')
                job_id = submit_job(self.bids.root_dir, sub, ses, self.job_json, args=args, use_asyncssh=True, passphrase=passphrase, check_if_exist=False)
                # job_id = ['Submitted batch job 2447621']
                if job_id is not None and job_id != []:
                    jobs_id.append(*job_id)
    
            except Exception as e:
                self.error_handler(e)
        
        self.is_in_progress(('AddServer', False))
        self.submitted_jobs(jobs_id)
    
    def is_in_progress(self, in_progress):
        self.parent.parent.work_in_progress.update_work_in_progress(in_progress)
        
    
    def error_handler(self, exception):
        QMessageBox.critical(self, type(exception).__name__, str(exception))
        
    def submitted_jobs(self, jobs_id):
        print('submitted jobs')
        class SubmittedJobsDialog(QDialog):
            def __init__(self, results, parent=None):
                super().__init__()
        
                self.setWindowTitle('Jobs Submitted')
                self.setGeometry(300, 300, 400, 300)
                
                layout = QVBoxLayout(self)
                
                # Create and populate the QListWidget
                self.listWidget = QListWidget(self)
                for result in results:
                    self.listWidget.addItem(result)
                
                layout.addWidget(self.listWidget)
        
                # Create OK button
                self.okButton = QPushButton('OK', self)
                self.okButton.clicked.connect(self.accept)
                
                # Add OK button to layout
                buttonLayout = QHBoxLayout()
                buttonLayout.addStretch()
                buttonLayout.addWidget(self.okButton)
                
                layout.addLayout(buttonLayout)
                
        job_dialog = SubmittedJobsDialog(jobs_id)
        # job_submitted_window = QMainWindow()
        # job_submitted_window.setCentralWidget(job_dialog)
        job_dialog.exec_()
    

    def end_add(self):
        """


        Returns
        -------
        None.

        """
        self.parent.parent.bids_metadata.update_metadata()
        logging.info(f'All done.')
        self.parent.setEnabled(True)


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
        
        
        
class JobTab(QWidget):
    """
    """
    
    def __init__(self, parent, slurm_infos):
        """
        

        Returns
        -------
        None.

        """
        super().__init__()
        
        self.parent = parent
        self.bids = self.parent.bids
        self.slurm_info = slurm_infos
        self.setMinimumSize(500, 200)
        self.slurm_info_input = {}
        layout = QVBoxLayout()
        for key in self.slurm_info.keys():
            key_label = QLabel(key)
            key_input = QLineEdit(self)
            key_input.setPlaceholderText(self.slurm_info[key])
            key_layout = QHBoxLayout()
            self.slurm_info_input[f'{key}_input'] = key_input
            key_layout.addWidget(key_label)
            key_layout.addWidget(key_input)
            layout.addLayout(key_layout)
            
        self.setLayout(layout)
            
            
    def get_slurm_job_info(self):
        
        slurm_job_info = {}
        for key in self.slurm_info.keys():
            key_text = self.slurm_info_input[f'{key}_input'].text()
            if key_text == None or key_text == "":
                key_text = self.slurm_info_input[f'{key}_input'].placeholderText()
                
            slurm_job_info[key] = key_text
        
        return slurm_job_info
        


# =============================================================================
# Rename
# =============================================================================
class Rename(QMainWindow):
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
        # self.threads_pool = self.parent.threads_pool

        self.setWindowTitle("Rename Subject/Session/Sequence")
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.center()

        self.tabs = QTabWidget(self)
        # Tab1
        self.tab1 = RenameSubject(self)

        # Tab 2
        # self.tab2 = RenameSession(self)

        # Tab 3
        self.tab3 = RenameSequence(self)

        self.tabs.addTab(self.tab1, "Subject")
        # self.tabs.addTab(self.tab2, "Session")
        self.tabs.addTab(self.tab3, "Sequence")

        # self.registration = TransformationTab(self)

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)

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
# RenameSubject
# =============================================================================
class RenameSubject(QMainWindow):
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
        # self.threads_pool = self.parent.threads_pool

        self.setWindowTitle("Rename Subject")
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.center()

        self.old_sub = QLineEdit(self)
        self.old_sub.setPlaceholderText("Old Subject ID")
        self.old_ses = QLineEdit(self)
        self.old_ses.setPlaceholderText("Old Session ID")
        self.new_sub = QLineEdit(self)
        self.new_sub.setPlaceholderText("New Subject ID")
        self.new_ses = QLineEdit(self)
        self.new_ses.setPlaceholderText("New Session ID")
        self.rename_button = QPushButton("Rename Subject")
        self.rename_button.clicked.connect(self.rename)

        layout = QGridLayout()
        layout.addWidget(self.old_sub, 0, 0, 1, 1)
        layout.addWidget(self.new_sub, 0, 1, 1, 1)
        layout.addWidget(self.old_ses, 1, 0, 1, 1)
        layout.addWidget(self.new_ses, 1, 1, 1, 1)
        layout.addWidget(self.rename_button, 2, 0, 1, 2)

        self.window.setLayout(layout)


    def rename(self):
        """


        Returns
        -------
        None.

        """
        print('rename subject')
        old_sub = self.old_sub.text()
        old_ses = self.old_ses.text()
        new_sub = self.new_sub.text()
        new_ses = self.new_ses.text()

        self.parent.setEnabled(False)
        self.thread = QThread()
        self.operation = OperationWorker(self.bids.rename_subject, args=[old_sub, old_ses, new_sub, new_ses])
        self.operation.moveToThread(self.thread)
        self.thread.started.connect(self.operation.run)
        self.operation.in_progress.connect(self.is_in_progress)
        self.operation.finished.connect(self.thread.quit)
        self.operation.finished.connect(self.operation.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        self.thread.finished.connect(
            lambda: self.parent.setEnabled(True)
        )
        print(f"sub-{old_sub} renamed to sub-{new_sub}")

        self.parent.hide()
        
        
    def is_in_progress(self, in_progress):
        self.parent.parent.parent.work_in_progress.update_work_in_progress(in_progress)


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
# ReneameSession
# =============================================================================
class RenameSession(QMainWindow):
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
        # self.threads_pool = self.parent.threads_pool

        self.setWindowTitle("Rename Session")
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.center()

        self.sub = QLineEdit(self)
        self.sub.setPlaceholderText("Subject ID")
        self.old_ses = QLineEdit(self)
        self.old_ses.setPlaceholderText("Old Session")
        self.new_ses = QLineEdit(self)
        self.new_ses.setPlaceholderText("New Session")
        self.rename_button = QPushButton("Rename Session")
        self.rename_button.clicked.connect(self.rename)

        layout = QGridLayout()
        layout.addWidget(self.sub, 0, 0, 1, 1)
        layout.addWidget(self.old_ses, 0, 1, 1, 1)
        layout.addWidget(self.new_ses, 1, 1, 1, 1)
        layout.addWidget(self.rename_button, 2, 0, 1, 2)

        self.window.setLayout(layout)


    def rename(self):
        """


        Returns
        -------
        None.

        """
        sub = self.sub.text()
        old_ses = self.old_ses.text()
        new_ses = self.new_ses.text()

        self.parent.setEnabled(False)
        self.thread = QThread()
        self.operation = OperationWorker(self.bids.rename_session, args=[sub, old_ses, new_ses])
        self.operation.moveToThread(self.thread)
        self.thread.started.connect(self.operation.run)
        self.operation.in_progress.connect(self.is_in_progress)
        self.operation.finished.connect(self.thread.quit)
        self.operation.finished.connect(self.operation.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        self.thread.finished.connect(
            lambda: self.parent.setEnabled(True)
        )
        logging.info(f"ses-{old_ses} renamed to ses-{new_ses} for sub-{sub}")

        self.hide()
        
        
    def is_in_progress(self, in_progress):
        self.parent.parent.parent.work_in_progress.update_work_in_progress(in_progress)


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
# RenameSequence
# =============================================================================
class RenameSequence(QMainWindow):
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
        # self.threads_pool = self.parent.threads_pool

        self.setWindowTitle("Rename Sequence")
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.center()

        self.old_seq = QLineEdit(self)
        self.old_seq.setPlaceholderText("Old Sequence")
        self.new_seq = QLineEdit(self)
        self.new_seq.setPlaceholderText("New Sequence")
        self.rename_button = QPushButton("Rename Sequence")
        self.rename_button.clicked.connect(self.rename_seq)

        layout = QGridLayout()
        layout.addWidget(self.old_seq, 0, 0, 1, 1)
        layout.addWidget(self.new_seq, 0, 1, 1, 1)
        layout.addWidget(self.rename_button, 1, 0, 1, 2)

        self.window.setLayout(layout)


    def rename_seq(self):
        """


        Returns
        -------
        None.

        """
        old_seq = self.old_seq.text()
        new_seq = self.new_seq.text()

        self.parent.setEnabled(False)
        self.thread = QThread()
        self.operation = OperationWorker(self.bids.rename_sequence, args=[old_seq, new_seq])
        self.operation.moveToThread(self.thread)
        self.thread.started.connect(self.operation.run)
        self.operation.in_progress.connect(self.is_in_progress)
        self.operation.finished.connect(self.thread.quit)
        self.operation.finished.connect(self.operation.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        self.thread.finished.connect(
            lambda: self.parent.setEnabled(True)
        )
        logging.info(f"old {old_seq} renamed to new {new_seq}")

        self.parent.hide()
        
        
    def is_in_progress(self, in_progress):
        self.parent.parent.parent.work_in_progress.update_work_in_progress(in_progress)


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
# UpdateDatasetDescription
# =============================================================================
class UpdateDatasetDescription(QMainWindow):
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
        # self.threads_pool = self.parent.threads_pool
        self.setMinimumSize(QSize(750,650))

        self.setWindowTitle("Update Dataset Description")
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.center()
        
        self.dataset_description = self.bids.get_dataset_description()

        self.tabs = QTabWidget(self)
        
        self.required_tab = UpdateDatasetDescription_RequiredTab(self)
        self.tabs.addTab(self.required_tab, "Required")
        
        self.recommended_tab = UpdateDatasetDescription_RecommendedTab(self)
        scroll_area_recommended_tab = QScrollArea()
        scroll_area_recommended_tab.setWidget(self.recommended_tab)
        scroll_area_recommended_tab.setWidgetResizable(True)
        scroll_area_recommended_tab.setAutoFillBackground(True)
        scroll_area_recommended_tab.setBackgroundRole(QPalette.Base)
        self.tabs.addTab(scroll_area_recommended_tab, "Recommended")
        
        self.optional_tab = UpdateDatasetDescription_OptionalTab(self)
        self.tabs.addTab(self.optional_tab, "Optional")

        self.update_dataset_description_button = QPushButton("Update Dataset Description")
        self.update_dataset_description_button.clicked.connect(self.update_dataset_description)
        
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(self.update_dataset_description_button)

        self.window.setLayout(layout)
        
        
    def update_dataset_description(self):
        """


        Returns
        -------
        None.

        """
        required_dic = self.required_tab.get_values()
        recommended_dic = self.recommended_tab.get_values()
        optional_dic = self.optional_tab.get_values()
        new_dataset_description = dict(required_dic, **recommended_dic, **optional_dic)
                
        self.parent.setEnabled(False)
        self.thread = QThread()
        self.operation = OperationWorker(self.bids.update_dataset_description, args=[], kwargs={'dataset_description':new_dataset_description})
        self.operation.moveToThread(self.thread)
        self.thread.started.connect(self.operation.run)
        self.operation.in_progress.connect(self.is_in_progress)
        self.operation.finished.connect(self.thread.quit)
        self.operation.finished.connect(self.operation.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        self.thread.finished.connect(
            lambda: self.parent.setEnabled(True)
        )
        self.thread.finished.connect(self.update_metadata)

        self.hide()
        
        
    def is_in_progress(self, in_progress):
        self.parent.work_in_progress.update_work_in_progress(in_progress)


    def update_metadata(self):
        self.parent.bids_metadata.update_metadata()


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
# UpdateDatasetDescription Required Tab
# =============================================================================
class UpdateDatasetDescription_RequiredTab(QWidget):
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
        # self.threads_pool = self.parent.threads_pool
        self.dataset_description = self.parent.dataset_description
        
        name_lab = QLabel('The name of the dataset.')
        name_lab.setWordWrap(True)
        self.name = QLineEdit(self)
        if self.dataset_description.get('Name') == None or self.dataset_description.get('Name') == '':
            self.name.setPlaceholderText(self.parent.parent.bids_name_dir)
        else:
            self.name.setPlaceholderText(self.dataset_description.get('Name'))
        
        BIDSVersion_lab = QLabel('The version of the BIDS standard used (1.2.2 by default).')
        BIDSVersion_lab.setWordWrap(True)
        self.BIDSVersion = QLineEdit(self)
        if self.dataset_description.get('BIDSVersion') == None or self.dataset_description.get('BIDSVersion') == '':
            self.BIDSVersion.setPlaceholderText("BIDS Version of the dataset")
        else:
            self.BIDSVersion.setPlaceholderText(self.dataset_description.get('BIDSVersion'))
            
        vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)        

        layout = QVBoxLayout()
        layout.addWidget(name_lab)
        layout.addWidget(self.name)
        layout.addWidget(BIDSVersion_lab)
        layout.addWidget(self.BIDSVersion)
        layout.addItem(vertical_spacer)

        self.setLayout(layout)
        
        
    def get_values(self):
        required_dic = {}
        if self.name.text() != '':
            required_dic['Name'] = self.name.text()
        else:
            if self.dataset_description.get('Name') == None or self.dataset_description.get('Name') == '':
                required_dic['Name'] = self.parent.parent.bids_name_dir
            else:
                required_dic['Name'] = self.dataset_description.get('Name')
        if self.BIDSVersion.text() != '':
            required_dic['BIDSVersion'] = self.BIDSVersion.text()
        else:
            required_dic['BIDSVersion'] = self.dataset_description.get('BIDSVersion')
            
        return required_dic
        
        
        
# =============================================================================
# UpdateDatasetDescription Recommended Tab
# =============================================================================
class UpdateDatasetDescription_RecommendedTab(QWidget):
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
        # self.threads_pool = self.parent.threads_pool
        self.dataset_description = self.parent.dataset_description
                
        HEDVersion_lab = QLabel('If HED tags are used: The version of the HED schema used to validate HED tags for study.')
        HEDVersion_lab.setWordWrap(True)
        self.HEDVersion = QLineEdit(self)
        if self.dataset_description.get('HEDVersion') == None or self.dataset_description.get('HEDVersion') == '':
            self.HEDVersion.setPlaceholderText("HEDVersion")
        else:
            self.HEDVersion.setPlaceholderText(self.dataset_description.get('HEDVersion'))
        
        dataset_type_lab = QLabel('The interpretation of the dataset. For backwards compatibility, the default value is "raw". \nMust be one of: "raw", "derivative".')
        dataset_type_lab.setWordWrap(True)
        self.dataset_type = "raw"
        self.dataset_type_cb = QComboBox(self)
        self.dataset_type_cb.addItems(["raw", "derivatives"])
        self.dataset_type_cb.currentIndexChanged.connect(self.update_dataset_type)        
        
        license_lab = QLabel('The license for the dataset. The use of license name abbreviations is RECOMMENDED for specifying a license (see BIDS secification). The corresponding full license text MAY be specified in an additional LICENSE file.')
        license_lab.setWordWrap(True)
        self.license = QLineEdit(self)
        if self.dataset_description.get('License') == None or self.dataset_description.get('License') == '':     
            self.license.setPlaceholderText('License')
        else:
            self.license.setPlaceholderText(self.dataset_description.get('License'))
       
        generated_by_lab = QLabel('Used to specify provenance of the dataset.')
        generated_by_lab.setWordWrap(True)
        
        if self.dataset_description.get('GeneratedBy') == None or self.dataset_description.get('GeneratedBy') == "":
            self.generated_by = [{}]
        else:
            self.generated_by = self.dataset_description.get('GeneratedBy')
        
        generated_by_sa = QScrollArea()
        generated_by_sa.setWidgetResizable(True)
        generated_by_sa.setFixedHeight(300)
        generated_by_sa.setAutoFillBackground(True)
        generated_by_sa.setBackgroundRole(QPalette.Background)   
        
        generated_by_gb = QGroupBox()
        generated_by_gb.setBackgroundRole(QPalette.Background)
        self.generated_by_add_button = QPushButton('Add')
        self.generated_by_add_button.clicked.connect(lambda :self.add_generated_by_widget(dic={}))
        
        self.generated_by_layout = QVBoxLayout()
        
        for item in self.generated_by:
            self.add_generated_by_widget(dic=item)
            
        self.generated_by_layout.addWidget(self.generated_by_add_button)
            
        generated_by_gb.setLayout(self.generated_by_layout)
        
        generated_by_sa.setWidget(generated_by_gb)
        
        source_datasets_lab = QLabel('Used to specify provenance of the dataset.')
        source_datasets_lab.setWordWrap(True)
        
        if self.dataset_description.get('SourceDatasets') == None or self.dataset_description.get('SourceDatasets') == "":
            self.source_datasets = [{}]
        else:
            self.source_datasets = self.dataset_description.get('SourceDatasets')
        
        source_datasets_sa = QScrollArea()
        source_datasets_sa.setWidgetResizable(True)
        source_datasets_sa.setFixedHeight(300)
        source_datasets_sa.setAutoFillBackground(True)
        source_datasets_sa.setBackgroundRole(QPalette.Background)   
        
        source_datasets_gb = QGroupBox()
        source_datasets_gb.setBackgroundRole(QPalette.Background)
        self.source_datasets_add_button = QPushButton('Add')
        self.source_datasets_add_button.clicked.connect(lambda :self.add_source_datasets_widget(dic={}))
        
        self.source_datasets_layout = QVBoxLayout()
        
        for item in self.source_datasets:
            self.add_source_datasets_widget(dic=item)
            
        self.source_datasets_layout.addWidget(self.source_datasets_add_button)
            
        source_datasets_gb.setLayout(self.source_datasets_layout)
        
        source_datasets_sa.setWidget(source_datasets_gb)
        
        vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)  
        
        layout = QVBoxLayout()
        layout.addWidget(HEDVersion_lab)
        layout.addWidget(self.HEDVersion)
        layout.addWidget(dataset_type_lab)
        layout.addWidget(self.dataset_type_cb)
        layout.addWidget(license_lab)
        layout.addWidget(self.license)
        layout.addWidget(generated_by_lab)
        layout.addWidget(generated_by_sa)
        layout.addWidget(source_datasets_lab)
        layout.addWidget(source_datasets_sa)
        layout.addItem(vertical_spacer)

        self.setLayout(layout)
        
    
    def update_dataset_type(self, item):
        if item == 0:
            self.dataset_type = "raw"
        else:
            self.dataset_type = "derivatives"
            
            
    def add_generated_by_widget(self, dic={}):
        new_generated_by_widget = GeneratedByWidget(self, dic=dic)
        self.generated_by_layout.insertWidget(self.generated_by_layout.count()-1, new_generated_by_widget)
        
    
    def remove_generated_by_widget(self, widget):
        self.generated_by_layout.removeWidget(widget)
        widget.deleteLater()
        
        
    def add_source_datasets_widget(self, dic={}):
        new_source_dataset = SourceDatasetWidget(self, dic=dic)
        self.source_datasets_layout.insertWidget(self.source_datasets_layout.count()-1, new_source_dataset)
        
        
    def remove_source_datasets_widget(self, widget):
        self.source_datasets_layout.removeWidget(widget)
        widget.deleteLater()
            
            
    def get_values(self):
        recommended_dic = {}
        if self.HEDVersion.text() != '':
            recommended_dic['HEDVersion'] = self.HEDVersion.text()
        else:
            if self.dataset_description.get('HEDVersion') != None:
                recommended_dic['HEDVersion'] = self.dataset_description.get('HEDVersion')
        recommended_dic['DatasetType'] = self.dataset_type
        if self.license.text() != '':
            recommended_dic['License'] = self.license.text()
        else:
            if self.dataset_description.get('License') != None:
                recommended_dic['License'] = self.dataset_description.get('License')
                
        generated_by = []
        for i in range(self.generated_by_layout.count()-1):
            widget = self.generated_by_layout.itemAt(i).widget()
            generated_by.append(widget.get_values())
            
        recommended_dic['GeneratedBy'] = generated_by
        
        source_datasets = []
        for i in range(self.source_datasets_layout.count()-1):
            widget = self.source_datasets_layout.itemAt(i).widget()
            source_datasets.append(widget.get_values())
            
        recommended_dic['SourceDatasets'] = source_datasets

        return recommended_dic
        


# =============================================================================
# GeneratedBy Widget
# =============================================================================
class GeneratedByWidget(QWidget):
    """
    """
    
    
    def __init__(self, parent, dic={}):
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
        self.dataset_description = self.parent.dataset_description
        self.dic = dic
        
        self.delete_button = QPushButton('Delete')
        self.delete_button.clicked.connect(lambda : self.parent.remove_generated_by_widget(self))
        
        generated_by_name_lab = QLabel('Name of the pipeline or process that generated the outputs. Use "Manual" to indicate the derivatives were generated by hand, or adjusted manually after an initial run of an automated pipeline.')
        generated_by_name_lab.setWordWrap(True)
        self.generated_by_name = QLineEdit(self)
        if self.dic.get('Name') == None or self.dic.get('Name') == "":
            self.generated_by_name.setPlaceholderText("Name of the pipeline or process")
        else:
            self.generated_by_name.setPlaceholderText(self.dic.get('Name'))
        generated_by_version_lab = QLabel('Version of the pipeline.')
        generated_by_version_lab.setWordWrap(True)
        self.generated_by_version = QLineEdit(self)
        if self.dic.get('Version') == None or self.dic.get('Version') == "":
            self.generated_by_version.setPlaceholderText("Version of Pipelines")
        else:
            self.generated_by_version.setPlaceholderText(self.dic.get('Version'))
        generated_by_description_lab = QLabel('Plain-text description of the pipeline or process that generated the outputs (Recommended if Manual).')
        generated_by_description_lab.setWordWrap(True)
        self.generated_by_description = QLineEdit(self)
        if self.dic.get('Description') == None or self.dic.get('Description') == "":
            self.generated_by_description.setPlaceholderText("Description of the process that generated outputs")
        else:
            self.generated_by_description.setPlaceholderText(self.dic.get('Description'))
        generated_by_codeURL_lab = QLabel('URL where the code used to generate the dataset may be found.')
        generated_by_codeURL_lab.setWordWrap(True)
        self.generated_by_codeURL = QLineEdit(self)
        if self.dic.get('CodeURL') == None or self.dic.get('CodeURL') == "":
            self.generated_by_codeURL.setPlaceholderText("URL where the code used to generate the dataset")
        else:
            self.generated_by_codeURL.setPlaceholderText(self.dic.get('CodeURL'))
        generated_by_container_lab = QLabel('Used to specify the location and relevant attributes of software container image used to produce the dataset. ')
        generated_by_container_lab.setWordWrap(True)
        self.generated_by_container_widget = CollapsibleBox(parent=self, title='Container')
        if self.dic.get('Container') == None or self.dic.get('Container') == "":
            self.generated_by_container = {}
        else:
            self.generated_by_container = self.dic.get('Container')
        generated_by_container_type_lab = QLabel('Type of the Container.')
        self.generated_by_container_type = QLineEdit(self)
        if self.generated_by_container.get('Type') == None or self.generated_by_container.get('Type') == "":
            self.generated_by_container_type.setPlaceholderText("Type of the Container")
        else:
            self.generated_by_container_type.setPlaceholderText(self.generated_by_container.get('Type'))
        generated_by_container_tag_lab = QLabel("Tag of the Container")
        self.generated_by_container_tag = QLineEdit(self)
        if self.generated_by_container.get('Tag') == None or self.generated_by_container.get('Tag') == "":
            self.generated_by_container_type.setPlaceholderText("Tag of the Container")
        else:
            self.generated_by_container_type.setPlaceholderText(self.generated_by_container.get('Tag'))
        generated_by_container_uri_lab = QLabel("URI of the Container")
        self.generated_by_container_uri = QLineEdit(self)
        if self.generated_by_container.get('URI') == None or self.generated_by_container.get('URI') == "":
            self.generated_by_container_type.setPlaceholderText("URI of the Container")
        else:
            self.generated_by_container_type.setPlaceholderText(self.generated_by_container.get('URI'))
        container_layout = QVBoxLayout()
        container_layout.addWidget(generated_by_container_tag_lab)
        container_layout.addWidget(self.generated_by_container_tag)
        container_layout.addWidget(generated_by_container_type_lab)
        container_layout.addWidget(self.generated_by_container_type)
        container_layout.addWidget(generated_by_container_uri_lab)
        container_layout.addWidget(self.generated_by_container_uri)
        self.generated_by_container_widget.setContentLayout(container_layout)
        
        
        layout = QVBoxLayout()
        layout.addWidget(self.delete_button)
        layout.addWidget(generated_by_name_lab)
        layout.addWidget(self.generated_by_name)
        layout.addWidget(generated_by_version_lab)
        layout.addWidget(self.generated_by_version)
        layout.addWidget(generated_by_description_lab)
        layout.addWidget(self.generated_by_description)
        layout.addWidget(generated_by_codeURL_lab)
        layout.addWidget(self.generated_by_codeURL)
        layout.addWidget(generated_by_container_lab)
        layout.addWidget(self.generated_by_container_widget)
        
        self.setLayout(layout)
            
    
    def get_values(self):
        return_dic = {}
        
        if self.generated_by_name.text() != "":
            return_dic['Name'] = self.generated_by_name.text()
        else:
            return_dic['Name'] = self.dic.get('Name')
            
        if self.generated_by_version.text() != "":
            return_dic['Version'] = self.generated_by_version.text()
        else:
            return_dic['Version'] = self.dic.get('Version')
            
        if self.generated_by_description.text() != "":
            return_dic['Description'] = self.generated_by_description.text()
        else:
            return_dic['Description'] = self.dic.get('Description')
            
        if self.generated_by_codeURL.text() != "":
            return_dic['CodeURL'] = self.generated_by_codeURL.text()
        else:
            return_dic['CodeURL'] = self.dic.get('CodeURL')
            
        container_dic = {}
        
        if self.generated_by_container_type.text() != "":
            container_dic['Type'] = self.generated_by_container_type.text()
        else:
            container_dic['Type'] = self.generated_by_container.get('Type')
            
        if self.generated_by_container_tag.text() != "":
            container_dic['Tag'] = self.generated_by_container_tag.text()
        else:
            container_dic['Tag'] = self.generated_by_container.get('Tag')
            
        if self.generated_by_container_uri.text() != "":
            container_dic['URI'] = self.generated_by_container_uri.text()
        else:
            container_dic['URI'] = self.generated_by_container.get('URI')
            
        return_dic['Container'] = container_dic
        
        return return_dic
            
        
        
        
        
        
# =============================================================================
# SourceDatasetWidget
# =============================================================================
class SourceDatasetWidget(QWidget):
    """
    """
    
    def __init__(self, parent, dic={}):
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
        self.dataset_description = self.parent.dataset_description
        self.dic = dic

        self.delete_button = QPushButton('Delete')
        self.delete_button.clicked.connect(lambda : self.parent.remove_source_datasets_widget(self))
        
        url_lab = QLabel('URL of source dataset')
        url_lab.setWordWrap(True)
        self.url = QLineEdit(self)
        if self.dic.get('URL') == None or self.dic.get('URL') == "":
            self.url.setPlaceholderText("URL")
        else:
            self.url.setPlaceholderText(self.dic.get('URL'))
            
        doi_lab = QLabel('DOI of source dataset')
        doi_lab.setWordWrap(True)
        self.doi = QLineEdit(self)
        if self.dic.get('DOI') == None or self.dic.get('DOI') == "":
            self.doi.setPlaceholderText("DOI")
        else:
            self.doi.setPlaceholderText(self.dic.get('DOI'))
            
        version_lab = QLabel('Version of source dataset')
        version_lab.setWordWrap(True)
        self.version = QLineEdit(self)
        if self.dic.get('Version') == None or self.dic.get('Version') == "":
            self.version.setPlaceholderText("Version")
        else:
            self.version.setPlaceholderText(self.dic.get('Version'))
            
        layout = QVBoxLayout()
        layout.addWidget(self.delete_button)
        layout.addWidget(url_lab)
        layout.addWidget(self.url)
        layout.addWidget(doi_lab)
        layout.addWidget(self.doi)
        layout.addWidget(version_lab)
        layout.addWidget(self.version)
        
        self.setLayout(layout)
        
        
    def get_values(self):
        return_dic = {}
        
        if self.url.text() != "":
            return_dic['URL'] = self.url.text()
        else:
            return_dic['URL'] = self.dic.get('URL')
            
        if self.doi.text() != "":
            return_dic['DOI'] = self.doi.text()
        else:
            return_dic['DOI'] = self.dic.get('DOI')
            
        if self.version.text() != "":
            return_dic['Version'] = self.version.text()
        else:
            return_dic['Version'] = self.dic.get('Version')
        
        return return_dic
        

# =============================================================================
# UpdateDatasetDescription Optinal Tab
# =============================================================================
class UpdateDatasetDescription_OptionalTab(QWidget):
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
        # self.threads_pool = self.parent.threads_pool
        self.dataset_description = self.parent.dataset_description
        
        authors_lab = QLabel("List of individuals (separated by ',') who contributed to the creation/curation of the dataset.")
        authors_lab.setWordWrap(True)
        self.authors = QLineEdit(self)
        if self.dataset_description.get('Authors') == None or self.dataset_description.get('Authors') == '':
            self.authors.setPlaceholderText("Authors")
        else:
            self.authors.setPlaceholderText(''.join(str(author)+',' for author in self.dataset_description.get('Authors'))[:-1])
        
        acknowledgements_lab = QLabel('Text acknowledging contributions of individuals or institutions beyond those listed in Authors or Funding.')
        acknowledgements_lab.setWordWrap(True)
        self.acknowledgements = QLineEdit(self)
        if self.dataset_description.get('Acknowledgements') == None or self.dataset_description.get('Acknowledgements') == '':
            self.acknowledgements.setPlaceholderText("Acknowledgements")
        else:
            self.acknowledgements.setPlaceholderText(self.dataset_description.get('Acknowledgements'))
        
        how_to_acknoledge_lab = QLabel('Text containing instructions on how researchers using this dataset should acknowledge the original authors. This field can also be used to define a publication that should be cited in publications that use the dataset.')
        how_to_acknoledge_lab.setWordWrap(True)
        self.how_to_acknoledge = QLineEdit(self)
        if self.dataset_description.get('HowToAcknowledge') == None or self.dataset_description.get('HowToAcknowledge') == '':
            self.how_to_acknoledge.setPlaceholderText("How to Acknowledge")
        else:
            self.how_to_acknoledge.setPlaceholderText(self.dataset_description.get('HowToAcknowledge'))
        
        funding_lab = QLabel("List of sources of funding (grant numbers) (separated by ',').")
        funding_lab.setWordWrap(True)
        self.funding = QLineEdit(self)
        if self.dataset_description.get('Funding') == None or self.dataset_description.get('Funding') == '':
            self.funding.setPlaceholderText("Funding")
        else:
            self.funding.setPlaceholderText(''.join(str(author)+',' for author in self.dataset_description.get('Funding'))[:-1])
        
        ethics_approvals_lab = QLabel("List of ethics committee approvals (separated by ',') of the research protocols and/or protocol identifiers.")
        ethics_approvals_lab.setWordWrap(True)
        self.ethics_approvals = QLineEdit(self)
        if self.dataset_description.get('EthicsApprovals') == None or self.dataset_description.get('EthicsApprovals') == '':
            self.ethics_approvals.setPlaceholderText("Ethics Approvals")
        else:
            self.ethics_approvals.setPlaceholderText(''.join(str(author)+',' for author in self.dataset_description.get('EthicsApprovals'))[:-1])
        
        references_and_links_lab = QLabel("List of references to publications (separated by ',') that contain information on the dataset. A reference may be textual or a URI.")
        references_and_links_lab.setWordWrap(True)
        self.references_and_links = QLineEdit(self)
        if self.dataset_description.get('ReferencesAndLinks') == None or self.dataset_description.get('ReferencesAndLinks') == '':
            self.references_and_links.setPlaceholderText("References and Links")
        else:
            self.references_and_links.setPlaceholderText(''.join(str(author)+',' for author in self.dataset_description.get('ReferencesAndLinks'))[:-1])
        
        dataset_doi_lab = QLabel('The Digital Object Identifier of the dataset (not the corresponding paper).')
        dataset_doi_lab.setWordWrap(True)
        self.dataset_doi = QLineEdit(self)
        if self.dataset_description.get('DatasetDOI') == None or self.dataset_description.get('DatasetDOI') == '':
            self.dataset_doi.setPlaceholderText("Dataset DOI")
        else:
            self.dataset_doi.setPlaceholderText(self.dataset_description.get('DatasetDOI'))
        
        vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)  
        
        layout = QVBoxLayout()
        layout.addWidget(authors_lab)
        layout.addWidget(self.authors)
        layout.addWidget(acknowledgements_lab)
        layout.addWidget(self.acknowledgements)
        layout.addWidget(how_to_acknoledge_lab)
        layout.addWidget(self.how_to_acknoledge)
        layout.addWidget(funding_lab)
        layout.addWidget(self.funding)
        layout.addWidget(ethics_approvals_lab)
        layout.addWidget(self.ethics_approvals)
        layout.addWidget(references_and_links_lab)
        layout.addWidget(self.references_and_links)
        layout.addWidget(dataset_doi_lab)
        layout.addWidget(self.dataset_doi)
        layout.addItem(vertical_spacer)

        self.setLayout(layout)
        
        
    def get_values(self):
        optional_dic = {}
        if self.authors.text() != '':
            optional_dic['Authors'] = self.authors.text().split(',')
        else:
            if self.dataset_description.get('Authors') != None:
                optional_dic['Authors'] = self.dataset_description.get('Authors')
        if self.acknowledgements.text() != '':
            optional_dic['Acknowledgements'] = self.acknowledgements.text()
        else:
            if self.dataset_description.get('Acknowledgements') != None:
                optional_dic['Acknowledgements'] = self.dataset_description.get('Acknowledgements')
        if self.how_to_acknoledge.text() != '':
            optional_dic['HowToAcknowledge'] = self.how_to_acknoledge.text()
        else:
            if self.dataset_description.get('HowToAcknowledge') != None:
                optional_dic['HowToAcknowledge'] = self.dataset_description.get('HowToAcknowledge')
        if self.funding.text() != '':
            optional_dic['Funding'] = self.funding.text().split(',')
        else:
            if self.dataset_description.get('Funding') != None:
                optional_dic['Funding'] = self.dataset_description.get('Funding')
        if self.ethics_approvals.text() != '':
            optional_dic['EthicsApprovals'] = self.ethics_approvals.text().split(',')
        else:
            if self.dataset_description.get('EthicsApprovals') != None:
                optional_dic['EthicsApprovals'] = self.dataset_description.get('EthicsApprovals')
        if self.references_and_links.text() != '':
            optional_dic['ReferencesAndLinks'] = self.references_and_links.text().split(',')
        else:
            if self.dataset_description.get('ReferencesAndLinks') != None:
                optional_dic['ReferencesAndLinks'] = self.dataset_description.get('ReferencesAndLinks')
        if self.dataset_doi.text() != '':
            optional_dic['DatasetDOI'] = self.dataset_doi.text()
        else:
            if self.dataset_description.get('DatasetDOI') != None:
                optional_dic['DatasetDOI'] = self.dataset_description.get('DatasetDOI')
            
        return optional_dic
        



# # =============================================================================
# # UpdateDatasetDescription
# # =============================================================================
# class UpdateDatasetDescription(QMainWindow):
#     """
#     """


#     def __init__(self, parent):
#         """


#         Parameters
#         ----------
#         parent : TYPE
#             DESCRIPTION.

#         Returns
#         -------
#         None.

#         """
#         super().__init__()
#         self.parent = parent
#         self.bids = self.parent.bids
#         # self.threads_pool = self.parent.threads_pool

#         self.setWindowTitle("Update Authors")
#         self.window = QWidget(self)
#         self.setCentralWidget(self.window)
#         self.center()
        
#         self.name = QLineEdit(self)
#         self.name.setPlaceholderText("Name of the dataset")
        
#         self.BIDSVersion = QLineEdit(self)
#         self.BIDSVersion.setPlaceholderText("1.2.2")
        
#         self.HEDVersion = QLineEdit(self)
#         self.HEDVersion.setPlaceholderText("HEDVersion")
        
#         self.dataset_type = QInputDialog.getItem(self, "", "Dataset Type", ['raw', 'derivatives'])
        
#         self.license  = QLineEdit(self)
#         self.license.placeholderText('License')
        
#         self.authors = QLineEdit(self)
#         self.authors.setPlaceholderText("Authors")
        
#         self.acknowledgements = QLineEdit(self)
#         self.acknowledgements.setPlaceholderText("Acknowledgements")
        
#         self.how_to_acknoledge = QLineEdit(self)
#         self.how_to_acknoledge.setPlaceholderText("How to Acknowledge")
        
#         self.funding = QLineEdit(self)
#         self.funding.setPlaceholderText("Funding")
        
#         self.ethics_approvals = QLineEdit(self)
#         self.ethics_approvals.setPlaceholderText("Ethics Approvals")
        
#         self.references_and_links = QLineEdit(self)
#         self.references_and_links.setPlaceholderText("References and Links")
        
#         self.dataset_doi = QLineEdit(self)
#         self.dataset_doi.setPlaceholderText("Dataset DOI")
        
#         self.generated_by = QLineEdit(self)
#         self.generated_by.setPlaceholderText("Generated By")
        
#         self.source_datasets = QLineEdit(self)
#         self.source_datasets.setPlaceholderText("Source Dataset")
        
#         self.update_dataset_description_button = QPushButton("Update Dataset Description")
#         self.update_dataset_description_button.clicked.connect(self.update_dataset_description)

#         layout = QVBoxLayout()
#         layout.addWidget(self.authors)
#         layout.addWidget(self.update_authors_button)

#         self.window.setLayout(layout)


#     def update_authors(self):
#         """


#         Returns
#         -------
#         None.

#         """
#         authors = self.authors.text()
#         if ',' in authors:
#             authors_list = authors.split(',')
#         else:
#             authors_list = [authors]
#         self.parent.setEnabled(False)
#         self.thread = QThread()
#         self.operation = OperationWorker(self.bids.update_authors_to_dataset_description, args=[self.bids.root_dir], kwargs={'authors':authors_list})
#         logging.debug('OperationWorker instanciated')
#         self.operation.moveToThread(self.thread)
#         logging.debug('OperationWorker moved to thread')
#         self.thread.started.connect(self.operation.run)
#         logging.debug('Thread started and launching operation.run')
#         self.operation.finished.connect(self.thread.quit)
#         self.operation.finished.connect(self.operation.deleteLater)
#         self.thread.finished.connect(self.thread.deleteLater)
#         self.thread.start()
#         self.thread.finished.connect(
#             lambda: self.parent.setEnabled(True)
#         )
#         self.thread.finished.connect(lambda: self.end_update())
#         logging.info(f"Updating {authors} as BIDS directory authors")
#         self.parent.bids_metadata.update_metadata()

#         self.hide()


#     def end_update(self):
#         """


#         Returns
#         -------
#         None.

#         """
#         logging.info('Thread ended')
#         self.parent.bids_metadata.update_metadata()


#     def center(self):
#         """


#         Returns
#         -------
#         None.

#         """
#         qr = self.frameGeometry()
#         cp = QDesktopWidget().availableGeometry().center()
#         qr.moveCenter(cp)
#         self.move(qr.topLeft())


# =============================================================================
# PandasModel
# =============================================================================
class PandasModel(QAbstractTableModel):
    DtypeRole = Qt.UserRole + 1000
    ValueRole = Qt.UserRole + 1001

    def __init__(self, df=pd.DataFrame(), parent=None):
        super(PandasModel, self).__init__(parent)
        self._dataframe = df
        self.editable = False

    def setDataFrame(self, dataframe):
        self.beginResetModel()
        self._dataframe = dataframe.copy()
        self.endResetModel()

    def dataFrame(self):
        return self._dataframe

    dataFrame = pyqtProperty(pd.DataFrame, fget=dataFrame, fset=setDataFrame)

    @pyqtSlot(int, Qt.Orientation, result=str)
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._dataframe.columns[section]
            else:
                return str(self._dataframe.index[section])
        return QVariant()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._dataframe.index)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return self._dataframe.columns.size

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount() \
            and 0 <= index.column() < self.columnCount()):
            return QVariant()
        row = self._dataframe.index[index.row()]
        col = self._dataframe.columns[index.column()]
        dt = self._dataframe[col].dtype

        val = self._dataframe.iloc[row][col]
        if role == Qt.DisplayRole:
            return str(val)
        elif role == PandasModel.ValueRole:
            return val
        if role == PandasModel.DtypeRole:
            return dt
        return QVariant()

    def roleNames(self):
        roles = {
            Qt.DisplayRole: b'display',
            PandasModel.DtypeRole: b'dtype',
            PandasModel.ValueRole: b'value'
        }
        return roles

    def flags(self, index):
        if self.editable:
            return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable
        else:
            return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsUserCheckable

    def setEditable(self, enable):
        self.editable = enable

    def setData(self, index, value, role):
        if value == '':
            return False
        if role == Qt.EditRole:
            self._dataframe.iloc[index.row(),index.column()] = value
            return True



# =============================================================================
# Table Viewer
# =============================================================================
class Table_Viewer(QWidget):
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
        # self.threads_pool = self.parent.threads_pool
        self.setMinimumSize(700,300)

        self.label = QLabel()
        self.label.setMinimumWidth(500)
        self.label.setFont(QFont('Calibri', 15))
        self.edit_button = QPushButton('Edit')
        self.edit_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'edit.png')))
        self.edit_button.adjustSize()
        self.edit_button.clicked.connect(self.edit)
        self.save_button = QPushButton('Save')
        self.save_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'save.png')))
        self.save_button.adjustSize()
        self.save_button.clicked.connect(self.save)
        self.close_button = QPushButton('Close')
        self.close_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'close.png')))
        self.close_button.adjustSize()
        self.close_button.clicked.connect(self.close)

        self.table_viewer = QTableView(self)
        # self.table_viewer.setOjectName('table_viewer')

        layout = QGridLayout()
        layout.addWidget(self.label, 0, 0, 1, 1)
        layout.addWidget(self.edit_button, 0, 1, 1, 1)
        layout.addWidget(self.save_button, 0, 2, 1, 1)
        layout.addWidget(self.close_button, 0, 4, 1, 1)
        layout.addWidget(self.table_viewer, 1, 0, 1, 5)

        self.setLayout(layout)

    def viewExcel(self, excel_file):
        self.excel_file = pjoin(excel_file)
        self.label.setText(os.path.split(pjoin(excel_file))[1])
        if '.xlsx' in excel_file:
            data = pd.read_excel(excel_file)
        elif '.tsv' in excel_file:
            data = pd.read_csv(excel_file, sep='\t')
        elif '.csv' in excel_file:
            data = pd.read_csv(excel_file)
        else:
            data = pd.DataFrame()

        data.fillna('n/a', inplace=True)

        self.model = PandasModel(data)
        self.table_viewer.setModel(self.model)
        self.table_viewer.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.table_viewer.resizeColumnsToContents()


    def edit(self):
        mode = self.edit_button.text()
        if mode == 'Edit':
            reply = QMessageBox.question(self, 'Edit?', 'Are you sure you want to edit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.model.setEditable(True)
                self.edit_button.setText('Stop Editing')
            else:
                return

        elif mode == 'Stop Editing':
            self.model.setEditable(False)
            self.edit_button.setText('Edit')
        else:
            pass


    def save(self):
        data = self.model._dataframe
        if '.xlsx' in self.excel_file:
            data.to_excel(self.excel_file, index=False)
        elif '.tsv' in self.excel_file:
            data.to_csv(self.excel_file, sep='\t', index=False)
        elif '.csv' in self.excel_file:
            data = to_csv(self.excel_file, index=False)
        else:
            pass


    def clean(self):
        self.label.setText('')
        self.model = PandasModel(pd.DataFrame())
        self.table_viewer.setModel(self.model)
        self.table_viewer.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.table_viewer.resizeColumnsToContents()


    def close(self):
        self.parent.updateViewer('default')
        
        
    def close_all(self):
        pass


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
# ParticipantsTSV Viewer
# =============================================================================
class ParticipantsTSV_Viewer(QWidget):
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
        # self.threads_pool = self.parent.threads_pool
        self.setMinimumSize(700,300)

        self.label = QLabel()
        self.label.setMinimumWidth(500)
        self.label.setFont(QFont('Calibri', 15))
        self.edit_button = QPushButton('Edit')
        self.edit_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'edit.png')))
        self.edit_button.adjustSize()
        self.edit_button.clicked.connect(self.edit)
        self.save_button = QPushButton('Save')
        self.save_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'save.png')))
        self.save_button.adjustSize()
        self.save_button.clicked.connect(self.save)
        self.plus_button = QPushButton('Add')
        self.plus_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'plus.png')))
        self.plus_button.adjustSize()
        self.plus_button.clicked.connect(self.add_item)
        self.close_button = QPushButton('Close')
        self.close_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'close.png')))
        self.close_button.adjustSize()
        self.close_button.clicked.connect(self.close)

        self.table_viewer = QTableView(self)
        # self.table_viewer.setOjectName('table_viewer')

        layout = QGridLayout()
        layout.addWidget(self.label, 0, 0, 1, 1)
        layout.addWidget(self.edit_button, 0, 1, 1, 1)
        layout.addWidget(self.save_button, 0, 2, 1, 1)
        layout.addWidget(self.plus_button, 0, 3, 1, 1)
        layout.addWidget(self.close_button, 0, 4, 1, 1)
        layout.addWidget(self.table_viewer, 1, 0, 1, 5)

        self.setLayout(layout)

    def viewExcel(self, excel_file):
        self.excel_file = pjoin(excel_file)
        self.label.setText(os.path.split(pjoin(excel_file))[1])
        if '.xlsx' in excel_file:
            data = pd.read_excel(excel_file)
        elif '.tsv' in excel_file:
            data = pd.read_csv(excel_file, sep='\t')
        elif '.csv' in excel_file:
            data = pd.read_csv(excel_file)
        else:
            data = pd.DataFrame()

        data.fillna('n/a', inplace=True)

        self.model = PandasModel(data)
        self.table_viewer.setModel(self.model)
        self.table_viewer.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.table_viewer.resizeColumnsToContents()


    def edit(self):
        mode = self.edit_button.text()
        if mode == 'Edit':
            reply = QMessageBox.question(self, 'Edit?', 'Are you sure you want to edit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.model.setEditable(True)
                self.edit_button.setText('Stop Editing')
            else:
                return

        elif mode == 'Stop Editing':
            self.model.setEditable(False)
            self.edit_button.setText('Edit')
        else:
            pass


    def save(self):
        data = self.model._dataframe
        if '.xlsx' in self.excel_file:
            data.to_excel(self.excel_file, index=False)
        elif '.tsv' in self.excel_file:
            data.to_csv(self.excel_file, sep='\t', index=False)
        elif '.csv' in self.excel_file:
            data = to_csv(self.excel_file, index=False)
        else:
            pass


    def clean(self):
        self.label.setText('')
        self.model = PandasModel(pd.DataFrame())
        self.table_viewer.setModel(self.model)
        self.table_viewer.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.table_viewer.resizeColumnsToContents()


    def close(self):
        self.parent.updateViewer('default')
        
        
    def close_all(self):
        pass


    def add_item(self):
        print("add_item")
        if hasattr(self, 'addWindow'):
            self.addWindow.deleteLater()
        self.addWindow = ParticipantsTSV_AddItem(self)
        self.addWindow.show()


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
# ParticipantsTSV_AddItem
# =============================================================================
class ParticipantsTSV_AddItem(QMainWindow):
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
        # self.threads_pool = self.parent.threads_pool

        self.setWindowTitle("Add item to participants.tsv")
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.center()

        self.name = QLineEdit(self)
        self.name.setPlaceholderText("Name")
        self.description = QLineEdit(self)
        self.description.setPlaceholderText('Description')
        self.dicom_tags = QLineEdit(self)
        self.dicom_tags.setPlaceholderText('DICOM tags')

        self.add_item_button = QPushButton("Add")
        self.add_item_button.clicked.connect(self.add_item)

        layout = QVBoxLayout()
        layout.addWidget(self.name)
        layout.addWidget(self.description)
        layout.addWidget(self.dicom_tags)
        layout.addWidget(self.add_item_button)

        self.window.setLayout(layout)


    def add_item(self):
        """


        Returns
        -------
        None.

        """
        name = self.name.text()
        description = self.description.text()
        dicom_tags = self.dicom_tags.text()
        dicom_tags = dicom_tags.split(',')

        new_item = {'name':name, 'infos':{'Description':description, 'dicom_tags':dicom_tags}}

        self.parent.setEnabled(False)
        self.thread = QThread()
        self.operation = OperationWorker(self.bids.update_participants_json, args=[new_item])
        self.operation.moveToThread(self.thread)
        self.thread.started.connect(self.operation.run)
        self.operation.in_progress.connect(self.is_in_progress)
        self.operation.finished.connect(self.thread.quit)
        self.operation.finished.connect(self.operation.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        self.thread.finished.connect(
            lambda: self.parent.setEnabled(True)
        )
        # self.thread.finished.connect(lambda: self.end_update())
        logging.info(f"Updating participants_json")
        # self.parent.bids_metadata.update_metadata()

        self.hide()
        
        
    def is_in_progress(self, in_progress):
        self.parent.parent.work_in_progress.update_work_in_progress(in_progress)


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
# Text Viewer
# =============================================================================
class TextViewer(QWidget):
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
        # self.threads_pool = self.parent.threads_pool
        self.setMinimumSize(700,300)

        self.label = QLabel()
        self.label.setMinimumWidth(500)
        self.label.setFont(QFont('Calibri', 15))
        self.edit_button = QPushButton('Edit')
        self.edit_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'edit.png')))
        self.edit_button.adjustSize
        self.edit_button.clicked.connect(self.edit)
        self.save_button = QPushButton('Save')
        self.save_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'save.png')))
        self.save_button.adjustSize
        self.save_button.clicked.connect(self.save)
        self.close_button = QPushButton('Close')
        self.close_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'close.png')))
        self.close_button.adjustSize()
        self.close_button.clicked.connect(self.close)

        self.text_viewer = QTextEdit(self)
        self.text_viewer.setReadOnly(True)
        # self.table_viewer.setOjectName('table_viewer')

        layout = QGridLayout()
        layout.addWidget(self.label, 0, 0, 1, 1)
        layout.addWidget(self.edit_button, 0, 1, 1, 1)
        layout.addWidget(self.save_button, 0, 2, 1, 1)
        layout.addWidget(self.close_button, 0, 3, 1, 1)
        layout.addWidget(self.text_viewer, 1, 0, 1, 4)

        self.setLayout(layout)


    def viewText(self, file):
        self.file = pjoin(file)
        self.label.setText(os.path.split(self.file)[1])
        # if '.json' in self.file:
        #     pass
        # elif '.txt' in self.file:
        #     pass

        with open(self.file, 'r') as f:
            self.text_viewer.insertPlainText(f.read())


    def edit(self):
        mode = self.edit_button.text()
        if mode == 'Edit':
            reply = QMessageBox.question(self, 'Edit?', 'Are you sure you want to edit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.text_viewer.setReadOnly(False)
                self.edit_button.setText('Stop Editing')
            else:
                return

        elif mode == 'Stop Editing':
            self.text_viewer.setReadOnly(True)
            self.edit_button.setText('Edit')
        else:
            pass


    def save(self):
        with open(self.file, 'w') as yourFile:
            yourFile.write(str(self.text_viewer.toPlainText()))


    def close(self):
        self.parent.updateViewer('default')
        
    
    def close_all(self):
        pass


    def clean(self):
        self.text_viewer.setText('')
        self.label.setText('')



# =============================================================================
# Default Viewer
# =============================================================================
class DefaultViewer(QWidget):
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
        # self.threads_pool = self.parent.threads_pool
        self.setMinimumSize(700,300)

        self.label = QLabel(self)
        self.label.setMinimumWidth(500)
        self.label.setFont(QFont('Calibri', 15))

        image = QLabel(self)
        image.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(pjoin(get_executable_path(), 'Pictures', 'bids_icon.png'))
        pixmap = pixmap.scaled(700, 500, Qt.KeepAspectRatio)
        image.setPixmap(pixmap)

        # # Optional, resize window to image size
        # self.resize(pixmap.width(),pixmap.height())

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(image)

        self.setLayout(layout)


    def setLabel(self, text):
        self.label.setText(os.path.split(pjoin(text))[1])

    def clean(self):
        self.label.setText('')
        
        
    def close_all(self):
        pass



# =============================================================================
# Default Nifti Viewer
# =============================================================================
class DefaultNiftiViewer(QWidget):
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
        # self.threads_pool = self.parent.threads_pool
        self.setMinimumSize(700,300)

        self.label = QLabel(self)
        self.label.setMinimumWidth(633)
        self.label.setFont(QFont('Calibri', 15))

        self.close_button = QPushButton('Close')
        self.close_button.setIcon(QIcon(pjoin(get_executable_path(), 'Pictures', 'close.png')))
        self.close_button.adjustSize()
        self.close_button.clicked.connect(self.close)

        # Creation of a figure
        # self.fig = Figure(figsize=(5.5,5.5))
        self.fig = plt.figure(figsize=(5.5,5.5))

        self.nifti_canvas = FigureCanvas(self.fig)

        # # Optional, resize window to image size
        # self.resize(pixmap.width(),pixmap.height())

        layout = QGridLayout()
        layout.addWidget(self.label, 0, 0, 1, 1)
        layout.addWidget(self.close_button, 0, 1, 1, 1)
        layout.addWidget(self.nifti_canvas, 1, 0, 1, 2, Qt.AlignCenter)

        self.setLayout(layout)


    def setLabel(self, file):
        self.label.setText(os.path.split(pjoin(file))[1])


    def viewNifti(self, nifti):
        self.setLabel(nifti)
        mri = nib.load(nifti)
        mri = mri.get_fdata()
        mri = np.rot90(mri, axes=(0,1))
        size = np.shape(mri)
        if len(size) == 2:
            # self.fig.figimage(mri, cmap='gray')
            plt.imshow(mri, cmap='gray', aspect='equal')
        elif len(size) == 3:
            if size[2] == 3 or size[2] == 4:
                # self.fig.figimage(mri)
                plt.imshow(mri, aspect='equal')
            else:
                # self.fig.figimage(mri[:,:,int(2*size[2]/4)], cmap='gray')
                if size[0] < size[1] and size[0] < size[2]:
                    plt.imshow(mri[int(2*size[0]/4),:,:], cmap='gray', aspect='equal')
                elif size[1] < size[0] and size[1] < size[2]:
                    plt.imshow(mri[:,int(2*size[1]/4),:], cmap='gray', aspect='equal')
                else:
                    plt.imshow(mri[:,:,int(2*size[2]/4)], cmap='gray', aspect='equal')
        elif len(size) == 4:
            if size[3] == 3 or size[3] == 4:
                # self.fig.figimage(mri)
                plt.imshow(mri, aspect='equal')
            else:
                # self.fig.figimage(mri[:,:,int(2*size[2]/4),0], cmap='gray')
                if size[0] < size[1] and size[0] < size[2]:
                    plt.imshow(mri[int(2*size[0]/4),:,:,0], cmap='gray', aspect='equal')
                elif size[1] < size[0] and size[1] < size[2]:
                    plt.imshow(mri[:,int(2*size[1]/4),:,0], cmap='gray', aspect='equal')
                else:
                    plt.imshow(mri[:,:,int(2*size[2]/4),0], cmap='gray', aspect='equal')
        else:
            return
        self.nifti_canvas.draw()


    def clean(self):
        self.label.setText('')
        self.fig.figimage(None)
        self.nifti_canvas.draw()


    def close(self):
        self.parent.updateViewer('default')
        
        
    def close_all(self):
        plt.close(self.fig)


# =============================================================================
# SubprocessWorker
# =============================================================================
class SubprocessWorker(QObject):
    """
    """
    finished = pyqtSignal()
    in_progress = pyqtSignal(tuple)


    def __init__(self, operation):
        """


        Parameters
        ----------
        operation : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        super().__init__()
        self.operation = operation

    def run(self):
        """


        Returns
        -------
        None.

        """
        operation = self.operation.split(' ')[0]
        self.in_progress.emit((operation, True))
        subprocess.Popen(self.operation, shell=True).wait()
        self.in_progress.emit((operation, False))
        self.finished.emit()
        
        
        
# =============================================================================
# AddPipelineWorker
# =============================================================================
class AddPipelineWorker(QObject):
    """
    """
    finished = pyqtSignal()
    in_progress = pyqtSignal(tuple)


    def __init__(self, repo):
        """


        Parameters
        ----------
        operation : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        super().__init__()
        self.repo = repo

    def run(self):
        """


        Returns
        -------
        None.

        """
        print('Add Pipeline Worker: Run')
        self.in_progress.emit((f'Add {self.repo.get("Name")}', True))
        
        git_url = f'https://github.com/BMAT-Apps/{self.repo.get("Name")}.git'
        
        pipeline_path = f'Pipelines/{self.repo.get("Name")}'
        
        self.in_progress.emit(('Clone repo', True))
        
        subprocess.Popen(f'git clone {git_url} {pipeline_path}', shell=True).wait()
        
        self.in_progress.emit(('Clone repo', False))
        
        self.in_progress.emit(('python requirements', True))
        
        with open(f'{pipeline_path}/setup.json') as json_file:
            setup = json.load(json_file)
        
        if setup.get('python_requirements') != None and setup.get('python_requirements') != "":
            requirements_path = f'{pipeline_path}/{setup.get("python_requirements")}'
            # subprocess.Popen(f'pip install -r {requirements_path}', shell=True).wait()
            install_requirements(requirements_path)
        
        self.in_progress.emit(('python requirements', False))
        
        self.in_progress.emit(('docker', True))
        
        if setup.get('docker') != None and setup.get('docker') != "":
            docker = setup.get('docker')
            if docker.get('docker') != None and setup.get('docker') != "":
                docker_name = docker.get('docker')
                if docker_name == 'DockerFile':
                    dockerfile_path = f'{pipeline_path}/Dockerfile'
                    subprocess.Popen(f'docker build -t {docker.get("tag")} -f {dockerfile_path} .', shell=True).wait()
                else:
                    subprocess.Popen(f'docker pull {docker_name}', shell=True).wait()
                    if docker.get('tag') != None and docker.get('tag') != "":
                        subprocess.Popen(f'docker tag {docker_name} {docker.get("tag")}', shell=True).wait()
        
        self.in_progress.emit(('docker', False))
        
        self.in_progress.emit((f'Add {self.repo.get("Name")}', False))
        self.finished.emit()
        
        
        
# =============================================================================
# UpdatePipelineWorker
# =============================================================================
class UpdatePipelineWorker(QObject):
    """
    """
    finished = pyqtSignal()
    in_progress = pyqtSignal(tuple)


    def __init__(self, repo):
        """


        Parameters
        ----------
        operation : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        super().__init__()
        self.repo = repo

    def run(self):
        """


        Returns
        -------
        None.

        """
        self.in_progress.emit((f'Update {self.repo.get("Name")}', True))
        
        # git_url = f'https://github.com/BMAT-Apps/{self.repo.get("Name")}.git'
        
        self.in_progress.emit(('Pull repo', True))
        
        pipeline_path = f'Piepelines/{self.repo.get("Name")}'
        
        subprocess.Popen(f'git -C {pipeline_path} pull', shell=True).wait()
        
        self.in_progress.emit(('Pull repo', False))
        
        self.in_progress.emit(('update python requirements', True))
        
        with open(f'Pipelines/{self.repo.get("Name")}/setup.json') as json_file:
            setup = json.load(json_file)
        
        if setup.get('python_requirements') != None and setup.get('python_requirements') != "":
            requirements_path = f'Pipelines/{self.repo.get("Name")}/{setup.get("python_requirements")}'
            subprocess.Popen(f'pip install -r {requirements_path}', shell=True).wait()
        
        self.in_progress.emit(('update python requirements', False))
        
        self.in_progress.emit(('update docker', True))
        
        if setup.get('docker') != None and setup.get('docker') != "":
            docker = setup.get('docker')
            if docker.get('docker') != None and setup.get('docker') != "":
                docker_name = docker.get('docker')
                if docker_name == 'DockerFile':
                    dockerfile_path = f'Pipelines/{self.repi.get("Name")}Dockerfile'
                    subprocess.Popen(f'docker build -t {docker.get("tag")} -f {dockerfile_path} .', shell=True).wait()
                else:
                    subprocess.Popen(f'docker pull {docker_name}', shell=True).wait()
                    if docker.get('tag') != None and docker.get('tag') != "":
                        subprocess.Popen(f'docker tag {docker_name} {docker.get("tag")}', shell=True).wait()
        
        self.in_progress.emit(('update docker', False))
        
        self.in_progress.emit((f'Update {self.repo.get("Name")}', False))
        self.finished.emit()



# =============================================================================
# OperationWorker
# =============================================================================
class OperationWorker(QObject):
    """
    """
    finished = pyqtSignal()
    in_progress = pyqtSignal(tuple)


    def __init__(self, function, args=[], kwargs={}):
        """


        Parameters
        ----------
        function : TYPE
            DESCRIPTION.
        args : TYPE, optional
            DESCRIPTION. The default is [].
        kwargs : TYPE, optional
            DESCRIPTION. The default is {}.

        Returns
        -------
        None.

        """
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs


    def run(self):
        """


        Returns
        -------
        None.

        """
        self.in_progress.emit((self.function.__name__, True))
        try:
            self.function(*self.args, **self.kwargs)
        except Exception as e:
            pass
        self.in_progress.emit((self.function.__name__, False))
        self.finished.emit()



# =============================================================================
# AddWorker
# =============================================================================
class AddWorker(QObject):
    """
    """
    finished = pyqtSignal()
    in_progress = pyqtSignal(tuple)

    def __init__(self, bids, list_to_add):
        """


        Parameters
        ----------
        bids : TYPE
            DESCRIPTION.
        list_to_add : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        super().__init__()
        self.bids = bids
        self.list_to_add = list_to_add


    def run(self):
        """


        Returns
        -------
        None.

        """
        self.in_progress.emit(('Add', True))
        
        for item in self.list_to_add:

            dicom = item[0]

            if ".zip" in dicom:
                directory_to_extract_to = dicom[:-4]
                with zipfile.ZipFile(dicom, 'r') as zip_ref:
                    zip_ref.extractall(directory_to_extract_to)
                dicom = directory_to_extract_to
    
            DICOM_FOLDER = dicom
            PATIENT_ID = item[1]
            SESSION = item[2]
    
            try:
                self.bids.convert_dicoms_to_bids(dicomfolder = DICOM_FOLDER,
                                                    pat_id      = PATIENT_ID,
                                                    session     = SESSION,
                                                    return_dicom_series=True)

            except Exception as e:
                pass
        
        # if ".zip" in dicom:
        #     # upload zip onto the cluster in a /tmp folder  
        #     pass
            
        self.in_progress.emit(('Add',False))    
        self.finished.emit()
        

# =============================================================================
# AddWorker
# =============================================================================
class AddServerWorker(QObject):
    """
    """
    finished = pyqtSignal()
    in_progress = pyqtSignal(tuple)
    error = pyqtSignal(Exception)
    jobs_submitted = pyqtSignal(list)

    def __init__(self, bids, list_to_add, iso, job_json, passphrase=None):
        """


        Parameters
        ----------
        bids : TYPE
            DESCRIPTION.
        list_to_add : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        super().__init__()
        self.bids = bids
        self.list_to_add = list_to_add
        self.iso = iso
        self.job_json = job_json
        self.passphrase = passphrase


    def run(self):
        """


        Returns
        -------
        None.

        """
        self.in_progress.emit(('AddServer', True))
        
        jobs_id = []
            
        for item in self.list_to_add:

            dicom = item[0]

            if not ".zip" in dicom:
                print ('Not a zip file')
                return 
    
            dicom_file = dicom
            sub = item[1]
            ses = item[2]
    
            try:
                args = [dicom_file]
                if self.iso:
                    args.append('-iso')
                job_id = submit_job(self.bids.root_dir, sub, ses, self.job_json, args, use_asyncssh=True, passphrase=self.passphrase)
                if job_id is not None and job_id != []:
                    jobs_id.append(*job_id)
    
            except Exception as e:
                self.error.emit(e)
        
        # if ".zip" in dicom:
        #     # upload zip onto the cluster in a /tmp folder  
        #     pass
        self.jobs_submitted.emit(jobs_id)
        self.in_progress.emit(('AddServer',False))    
        self.finished.emit()



# =============================================================================
# StdOutTextEdit
# =============================================================================
class StdOutTextEdit(QPlainTextEdit):
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
        super(StdOutTextEdit, self).__init__()
        self.setParent(parent)
        self.setReadOnly(True)
        self.setMinimumSize(700,300)


    @pyqtSlot(str)
    def append_text(self, text: str):
        """


        Parameters
        ----------
        text : str
            DESCRIPTION.

        Returns
        -------
        None.

        """
        self.moveCursor(QTextCursor.End)
        self.insertPlainText(text)



# =============================================================================
# StdTQDMTextEdit
# =============================================================================
class StdTQDMTextEdit(QLineEdit):
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
        super(StdTQDMTextEdit, self).__init__()
        self.setParent(parent)
        self.setReadOnly(True)
        self.setEnabled(True)
        self.setMinimumWidth(500)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setClearButtonEnabled(True)
        self.setFont(QFont('Consolas', 11))


    @pyqtSlot(str)
    def set_tqdm_text(self, text: str):
        """


        Parameters
        ----------
        text : str
            DESCRIPTION.

        Returns
        -------
        None.

        """
        new_text = text
        if new_text.find('\r') >= 0:
            new_text = new_text.replace('\r', '').rstrip()
            if new_text:
                self.setText(new_text)
        else:
            # we suppose that all TQDM prints have \r, so drop the rest
            pass



class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)

        self.toggle_button = QToolButton(
            text=title, checkable=True, checked=False
        )
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QParallelAnimationGroup(self)

        self.content_area = QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.content_area.setFrameShape(QFrame.NoFrame)
        self.content_area.setBackgroundRole(QPalette.Background)

        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self.content_area, b"maximumHeight")
        )

    @pyqtSlot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            Qt.DownArrow if not checked else Qt.RightArrow
        )
        self.toggle_animation.setDirection(
            QAbstractAnimation.Forward
            if not checked
            else QAbstractAnimation.Backward
        )
        if checked:
            self.toggle_button.setChecked(False)
        else:
            self.toggle_button.setChecked(True)
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)





def launch_BMAT():
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()

    # app = QApplication(sys.argv)

    window = MainWindow()

    window.show()

    app.exec()


if __name__ == "__main__":

    launch_BMAT()

    # if not QApplication.instance():
    #     app = QApplication(sys.argv)
    # else:
    #     app = QApplication.instance()

    # # app = QApplication(sys.argv)

    # window = MainWindow()

    # window.show()

    # app.exec()

    # del config_dict['TQDM_WRITE_STREAM_CONFIG']['queue']
    # del config_dict['TQDM_WRITE_STREAM_CONFIG']['write_stream']
    # del config_dict['TQDM_WRITE_STREAM_CONFIG']['qt_queue_receiver']
    # del config_dict['TQDM_WRITE_STREAM_CONFIG']
    # del config_dict['STDOUT_WRITE_STREAM_CONFIG']['queue']
    # del config_dict['STDOUT_WRITE_STREAM_CONFIG']['write_stream']
    # del config_dict['STDOUT_WRITE_STREAM_CONFIG']['qt_queue_receiver']
    # del config_dict['STDOUT_WRITE_STREAM_CONFIG']
    # del config_dict

    pass
