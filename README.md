# BIDS Managing and Analysis Tool

## Description

The BMAT software is a complete and easy-to-use local open-source neuroimaging analysis tool with a graphical user interface (GUI) that uses the BIDS format to organize and process brain MRI data for MS imaging research studies. BMAT provides the possibility to translate data from MRI scanners to the BIDS structure, create and manage BIDS datasets as well as develop and run automated processing pipelines. 

BMAT is now compatible to work with remote server using shared samba folder and a slurm scheduler to process data on remote server. It has to be noted that this feature has been implemented for users based in the Institute of NeuroSciences (IoNS) from UCLouvain. Therefore, it may not work easily with every servers, but feel free to fork the code and adapt it for your institue.

## Table of Contents

1. [Description](#description)
2. [How To Cite](#how-to-cite)
3. [Installation](#installation)
    * [Dependencies](#dependencies)
        * [Git](#git)
        * [Docker](#docker)
        * [ITK-snap](#itk-snap)
4. [Utilization](#utilization)
    * [Open/Create new BIDS](#opencreate-new-bids)
    * [Main Window](#main-window)
    * [Safe File Explorer](#safe-file-explorer)
    * [BIDS Actions](#bids-actions)
        * [Add Data](#add-data)
        * [Remove Data](#remove-data)
        * [Rename Subject/Session/Sequence](#rename-subjectsessionsequence)
    * [BIDS Menu](#bids-menu)
    * [Pipelines Menu](#pipelines-menu)
        * [Add New Pipelines](#add-new-pipelines)
        * [Available Pipelines](#available-pipelines)
    * [Local Pipelines](#local-pipelines)
        * [Adding Local Pipelines](#adding-local-pipelines)
5. [Server compatibility (UCLouvain/IoNS)](#server-compatibility-uclouvainions)
6. [Installation from Source Code](#installation-from-source-code)
    * [Dependencies](#dependencies-1)
        * [Python](#python)
            * [Linux](#linux)
            * [Windows](#windows)
            * [Mac](#mac)
        * [Docker](#docker-1)
        * [Git](#git-1)
        * [ITK-SNAP](#itk-snap-1)
    * [Installation process](#installation-process)
        * [Download BMAT](#download-bmat)
        * [Install python requirements](#install-python-requirements)
        * [Install docker required images](#install-docker-required-images)


# How To Cite: 
1. Vanden Bulcke, C. et al. BMAT: An open-source BIDS managing and analysis tool. NeuroImage: Clinical 36, 103252 (2022).

DOI: https://doi.org/10.1016/j.nicl.2022.103252

## Installation

BMAT can be downloaded as a Compiled version from the GitHub releases on the right. The compiled version has the advantages to be easy to install and stable. Here are the instructions on how to install BMAT on the different OS:

- Windows OS: go to the releases page, download the *BMAT_setup.exe*, run it as an administrator and install the application

- Linux: go to the releases page, download the compress *BMAT.tar.gz* file, decompress it with 
```
tar -xcvf BMAT.tar.gz
```

- MacOS: Unfortunately, due to the difficulty to develop and compile application on MacOS, BMAT is not available as a compiled application on MacOS. For Mac users, the only possibility is to download BMAT from source code (cf. [Install from source code](#installation-from-source-code))

BMAT has a few dependencies to work properly, i.e. Git, Docker, ITK-SNAP. You will find below the description on how to install each depedencies.

### Dependencies

Firstly, this section presents the different dependencies that need to be installed for this software to work properly. 

#### Git 

Git is free and open source software for distributed version control: tracking changes in any set of files, usually used for coordinating work among programmers collaboratively developing source code during software development. 

[Git](https://git-scm.com/downloads)


#### Docker 

Docker is a set of platforms as a service (PaaS) products that use OS-level virtualization to deliver software in packages called containers. The software that hosts the containers is called Docker Engine. BMAT uses docker containers to run analysis pipelines on the medical images. 

[Docker installation tutorial](https://docs.docker.com/get-docker/)

Docker installation process can be tedious on certain OS, especially on Windows and MacOSX. For Windows, you might have to change the backend of your OS to wsl2 ([instruction](https://learn.microsoft.com/en-us/windows/wsl/install-manual#step-4---download-the-linux-kernel-update-package)).


#### ITK-snap

ITK-SNAP is an easy-to-use 3D viewer for medical images (DICOM, NIfTI, etc.) and provides a great framework to perform segmentation of structure. BMAT uses this software to view the medical images. 

[ITK-SNAP installation tutorial](http://www.itksnap.org/pmwiki/pmwiki.php?n=Documentation.TutorialSectionInstallation)

**The installation of BMAT is now complete and the software is now ready to be launched**

The next section will show how to use this software.

Enjoy!

## Utilization

This section aims to explain how to use BMAT. 
A test DICOM MRI session of a healthy subject is available for download with this link [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7213153.svg)](https://doi.org/10.5281/zenodo.7213153)

### Open/Create new BIDS

When opening the software, a first window pops up and asks to select a BIDS dataset to launch BMAT. The user can either select a folder correponding to a BIDS dataset or create/select an empty folder to create a new BIDS dataset. 

![Openning Window](/Readme_Pictures/SelectBIDS.png)

### Main Window 

Here is a picture of the main window of BMAT. It is composed of these different windows:
* Safe File Explorer (left): allows the user to navigate the file that are inside his BIDS dataset
* Dataset Information (top center): contains information about the dataset
* Dataset Actions (top right): buttons to perform Actions on the dataset
* Quick Viewer (bottom right): Quick viewer to observe the file in the dataset in a safe manner
* BMAT menu: set preferences path for ITK-SNAP and dcm2niix
* BIDS menu (top left): contains other other actions to manage the dataset
* Pipelines menu (top left): add and run analysis pipelines shared by the BMAT-community
* Local Pipelines menu (top left): run local analysis pipelines implemented by the user

![Main Window](/Readme_Pictures/Main_Window.png)

### Safe File Explorer

This widget allows the user to navigate the files that are in his dataset in a safe manner, meaning that it prevents the user from unwantingly move and delete files. The user can also open the files in the quick viewer by double-clicking on a file to read the information they contain and edit them if wanted. There are also two particularities for specific types of files:
1. NIfTI files (.nii.gz) corresponding to images can be opened in the quick viewer by clicking one time on the file; this will show one slice of the image. By double clicking on the file, this will open the image in an ITK-SNAP window, which is a complete 3D viewer for 3D medical images. ITK-SNAP also contains some useful tools for neuroimaging studies; manual segmentation for instance. 
2. The *participants.tsv* file is a file that contains information about the subjects that are in the BIDS dataset. This file contains by default the subject participant_id, age, sex, and MRI session date. However, for neuroimaging studies, it is often useful to have other information on the subject. When opening the *participants.tsv* file in BMAT quick viewer, the software proposes a button **Add** to add information about the subject in this file. Indeed, the software is able to retrieve any information that is contained in the DICOM file. To do so, the user needs to give the software the name of this new information (this will be used for the name of the column), a description of this new information and the DICOM keyword that needs to be used to retrieve this information. The software will then retrieve this information in the DICOM of every subject in the database and keep this new information in the *participants.json* file. It will then automatically retrieve this new information for every new subject added to the dataset.

![Safe File Explorer](/Readme_Pictures/SafeFileExplorer.png)

### BIDS Actions

This section will describe the different features that BMAT integrates to manage a BIDS dataset. 

#### Add Data

When creating a new BIDS dataset, the first thing to do is to import new data in the dataset. BMAT allows the user to import entire MRI sessions at once instead of single sequences. Indeed, when a subject undergoes an MRI exam, he will often be scanned with different MRI sequences. An entire MRI session will contain the DICOM of the different sequences, all taken at the same day in series, in a specific folder. 

When clicking on the **Add** button, it will open a dedicated window for the user to select entire sessions of subjects to add to the dataset. The user can add specific folder containing the DICOM files or compressed folder in the ZIP format. Associated with each MRI session, the user can specify a corresponding subject ID and session NUMBER to use; this is especially useful when working with longitudinal studies to specify to the software that this session corresponds to a follow-up MRI session for a certain subject. Otherwise, by not specifying anything, the software will assume that this session corresponds to the first session of a new subject and will select a new available subject ID. By clicking on the **Add to BIDS** button, BMAT will automatically convert the DICOM files into the NIfTI format using *dicom2niix*, create the corresponding folders for this subject in the dataset, rename the files and store them in the right places in the dataset (the DICOM files are stored in the *sourcedata* folder and the NIfTI and json files in the corresponding subject folder. 

![Add Window](/Readme_Pictures/add_window.png)

For the renaming of the files, BMAT uses a keywords recognition scheme described in the *sequences.csv* file that is found in the *BMAT* folder. This must be completed by the user with information about the sequences that he uses, prior to the utilization of the software:
The renaming strategy is user-dependent and based on a mapping between the NIFTI file name after conversion with *dicom2niix* (mainly the *SeriesDescription* in the DICOM files) and the corresponding BIDS modality, described in the *sequences.csv* file. The mapping file needs only to be completed once at the beginning of the study and the software will then be able to recognize and work with these sequences. The mapping file works as follow; the software recognizes keywords in the file name and maps them to the corresponding BIDS name. The renaming scheme works in 3 steps: 
1. The software finds the modality of a sequence by trying one by one the different possible keyword(s) (one or several separated by ‘+’) in the modality column of the file and maps the matching keywords to the corresponding BIDS modality in the ‘modality_bids’ column.
2. Once the modality has been found, the software will check if other BIDS fields need to be completed by using a similar scheme on the modality sub table. It checks if a keyword from a BIDS field column (e.g. ‘acq’) lies in the filename and uses the corresponding BIDS label (in ‘acq_bids’ column) for the renaming. The user can add columns to the file corresponding to other BIDS field; one column named after the BIDS field with the specific keywords and the other with the ‘_bids’ extension that contains the corresponding label to use. An empty cell is not taken into account while a ‘_’ cell is always taken into account.
3. Finally, the MRI_type column contains the name of the subfolder in which this sequence needs to be stored. If the *IGNORED* keyword is used, the sequence will not be considered in the BIDS dataset. This is especially useful to not consider the Localization sequences that are used during the MRI exam to acquire the other sequences. 
The software is always trying the keywords from top to bottom of the file and stops as soon as it gets a match. This scheme means that it is up to the user to follow BIDS specification for the renaming of the sequences. The software will only validate the dataset as BIDS compliant or not. 

![sequences.csv file](/Readme_Pictures/sequences_csv.png)

#### Remove Data

This options allows the user to remove entire subjects or sessions from the dataset. BMAT will automatically remove all the data corresponding to this subject or session from the dataset. It will also asks the user if they want to delete the DICOM of this subject of the *sourcedata* folder. If not the DICOM will be moved to a dedicated folder in the *sourcedata* folder. 

#### Rename subject/session/sequence

This feeature allows the user to rename subject sessions or sequences in the dataset. When renaming a sequence, BMAT will automatically rename the sequence for all the subjetcs inside the dataset. 

### BIDS Menu

This menu contains some more features to manage the BIDS dataset. Here is a description of the different features:
* Create BIDS directory: this will open a similar window to the first one for the user to create a new empty folder to select and create a new empty BIDS dataset.
* Change BIDS directory: this will open a similar window to the first one for the user to select a new folder corresponding to a new BIDS dataset.
* BIDS Quality Control: this will run a *bids-validator* program that will give the user informations about the validity of his BIDS dataset according to the BIDS specifications as well as give a link towards the BIDS specifications
* Update Dataset Description: allows the user to update the name of the authors of the BIDS dataset. 

### Pipelines Menu

This menu allows the user to add and run pipelines to the software to automatically run analysis on the database. Pipelines that can be added have been implemented and shared by the BMAT-community through the [BMAT-Apps](https://github.com/orgs/BMAT-Apps) GitHub organization. The feature is describe in detail below:

#### Add new Pipelines

By clicking on the *Add New Pipeline* item from the *Pipelines* drop-down menu, this will open a window that shows all the different pipelines that can be found in the [BMAT-Apps](https://github.com/orgs/BMAT-Apps) GitHub organization (shown in Figure below).

![Add New Pipeline Window](/Readme_Pictures/AddNewPipeline.png)

The user can then click on any pipeline to open another specific window that shows the documentation of the pipeline, as can be found on GitHub (cf. Figure below). The user has the possibility to download the pipeline by clicking on the *Get Pipeline* button. 


#### Available pipelines

All the available pipelines can be found in the [BMAT-Apps](https://github.com/orgs/BMAT-Apps) GitHub organization. Here is a description of the available pipelines. 

### Local Pipelines

This feature allows the user to add and run its locally implemented pipelines on the database. To add a new local pipeline, the user must have knowledge in python and PyQt5. The process is explained below.

#### Adding Local pipelines

BMAT allows the user to add his own pipelines to the software to run specific in-house developed pipelines. To add a new Pipeline to the software, the user must add its source code in python, containing a dedicated graphical interface using PyQt5 and the computation code, as well as an associated JSON file containing metainformation about the pipeline, in the *NewPipelines* folder of the source code of the software. The JSON file must be written in a dictionary-like structure, as described in Figure 6 and contain the following pieces of information: 

* "name”: the name of the Pipeline that will be displayed in the ‘Pipelines’ drop-down menu in the software. 
* “source_code”: the name of the python file containing the source code for the graphical interface of the pipeline. This file needs to be implemented using PyQt5 python module and contain a launch function, that takes the Main Window of the software as only argument, and that launches the graphical interface of the Pipeline. User can take the Template pipeline as an example.
* “import_name”: the name of the corresponding module that needs to be imported in python. It corresponds to the name of the python source code file without the ‘.py’ extension.
* “attr”: the name of the attribute of the imported ‘Pipelines’ python module corresponding to the python source code of the pipeline. Again, this corresponds to the name of the python source code file without the ‘.py’ extension. 
* "add_info": this contains a dictionnary containing some specific information that the pipeline needs to run (e.g. the name of a sequence to use). 
    
The implementation of the computation part of the pipeline can use docker container or can be implemented locally, allowing adaptability of the software to a wide range of Neuroimaging applications.

## Server compatibility (UCLouvain/IoNS)

Speicific for UCLouvain/IoNS members, BMAT was implemented with a possibilities to connect to the remote SSS server to access and process your data on the server. 

1. First, make sure to have a SSH access to the server

2. In the BMAT home directory, update the server_info.json file with your specific information:
    * "server": 
        * "host": IP address of the server
        * "user": your user name
        * "key": path towards your ssh key do connect to the server
    * "shared_folders": list of all the connected shared samba folders on your system. This allows the program to map folder/files path on your computer to their location on the server

3. Update all pipeline option file (pipeline.json) to allow running pipelines on the server via the slurm scheduler. For that, in the pipeline.json file, make sure that there is a "sss_slurm" tag in the add_info dictionnary that points towards another json file contaitning the slurm job infos (script to run, environment, modules, job ressources, etc.)

## Installation from source code

This section aims at explaining how to download and install BMAT from source code. This software uses a lot of dependencies that need to be installed which can make the installation process a bit long and tedious. 

### Dependencies

Firstly, this section presents the different dependencies that need to be installed for this software to work properly. 

#### Python 

This software is written entirely in Python and thus requires Python to be installed to work properly. Pip is also needed to install the different packages that the software requires. Pip can sometimes be installed additionnaly when installing Python but not in every case, so it needs to be verified. The installation will be described for the different possible OS.

⚠️ **Python version should be >= 3.8** ⚠️

##### Linux

[Install Python on Linux](https://www.scaler.com/topics/python/install-python-on-linux/)

This link describes extensively how to install python on Linux. 

The easiest solution to install Python is to use the Package Manager. For this, open a terminal and type the following command: 

```
sudo apt-get install python
```

After the installation, you can verify that it all worked properly by typing:

```
python -V
```

This command should show you the version of Python. 

Then, you can check if pip has been installed by typing:

```
pip -V
```

If the command show you the version of pip, it means that it has been installed. Otherwise, it will say that 'pip' is not recognized and needs to be installed. To install pip, you can type in the terminal:

```
sudo apt-get install python-pip
```

This will install pip, you can check that pip is well installed by checking its version. 

##### Windows

The first possibility is to download Python via the microsoft store. This should download and install Python and Pip on your computer. To check if the installation has worked, you can open a command prompt or powershell and type:

```
python -V 
```

to see the version of python and 

```
pip -V
```

to see the verison of pip.

If there is no error, move on. 

The second possibility is to download the installation package directly on the [Python Website](https://www.python.org/downloads/windows/) and install it via the classic installation process. Following this method, pip will not be installed with python. Here are the steps to install pip:
1. Download the [get-pip.py](https://bootstrap.pypa.io/get-pip.py) script to a folder on your computer. 
2. Open a command prompt in that folder or navigate to that folder.
3. Run the script with the following command:

```
python get-pip.py
```

This should install pip. You can check if the installation worked by typing:

```
pip -V
```

##### Mac

Download the installation package directly from the [Python Website](https://www.python.org/downloads/macos/) and install it via the classic installation process. Following this method, pip will not be installed with python. Here are the steps to install pip:
1. Download the [get-pip.py](https://bootstrap.pypa.io/get-pip.py) script to a folder on your computer. 
2. Open a command prompt in that folder or navigate to that folder.
3. Run the script with the following command:

```
python get-pip.py
```

This should install pip. You can check if the installation worked by typing:

```
pip -V
```

#### Docker 

Docker is a set of platforms as a service (PaaS) products that use OS-level virtualization to deliver software in packages called containers. The software that hosts the containers is called Docker Engine. BMAT uses docker containers to run analysis pipelines on the medical images. 

[Docker installation tutorial](https://docs.docker.com/get-docker/)

Docker installation process can be tedious on certain OS, especially on Windows and MacOSX. For Windows, you might have to change the backend of your OS to wsl2 ([instruction](https://learn.microsoft.com/en-us/windows/wsl/install-manual#step-4---download-the-linux-kernel-update-package)).

#### Git 

Git is free and open source software for distributed version control: tracking changes in any set of files, usually used for coordinating work among programmers collaboratively developing source code during software development. 

[Git](https://git-scm.com/downloads)

#### ITK-snap

ITK-SNAP is an easy-to-use 3D viewer for medical images (DICOM, NIfTI, etc.) and provides a great framework to perform segmentation of structure. BMAT uses this software to view the medical images. 

[ITK-SNAP installation tutorial](http://www.itksnap.org/pmwiki/pmwiki.php?n=Documentation.TutorialSectionInstallation)

### Installation process

#### Download BMAT

Now that all the dependencies have been downloaded and installed, it is time to install BMAT. The first step is to download the software and you can either:

* If you have git, open a terminal and navigate to the folder you want to install BMAT and then clone this repository by typing: 

```
git clone https://github.com/ColinVDB/BMAT.git
```

* Otherwise, you can download a zip version of the code by clicking on the green Code button at the top right of this page, then **Download ZIP**. Afterwards, extract the Zip file in the folder where you want BMAT to be installed. 

The advantage of installing and using git becomes apparent when updating BMAT. You will able to easily do it by typing this command:

```
git pull
```

#### Install python requirements 

After having downloaded BMAT, you need to install all the required python module packages in order for the software to work properly. To do so, open a terminal and navigate into the BMAT folder,
```
cd BMAT
```
Then install the required packages using this command:
```
pip install -r requirements.txt
```

#### Install docker required images

The last part of the installation is to pull the different docker images used by the software. For this, make sure that the docker daemon socket is active. On Windows and Mac you will need to run Docker Desktop in the background for it to be active. To pull a docker image, open a terminal and type 'docker pull *name of the image to download*. There are 2 images that need to be pulled:

1. colinvdb/bmat-dcm2niix: this image is an docker extension of BMAT and contains [dcm2niix](https://github.com/rordenlab/dcm2niix), a program used to convert DICOM files to NIfTI, that the software requires to work properly like:
```
docker pull colinvdb/bmat-dcm2niix
```
2. bids/validator: this image is used to verify the BIDS validity of the datasets ([bids/validator](https://hub.docker.com/r/bids/validator))
```
docker pull bids/validator
```

**The installation of BMAT is now complete and the software is now ready to be launched**

The next section will show how to use this software.

