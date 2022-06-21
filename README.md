# BIDS Managing and Analysis Tool

## Description

The BMAT software is a complete and easy-to-use local open-source neuroimaging analysis tool with a graphical user interface (GUI) that uses the BIDS format to organize and process brain MRI data for MS imaging research studies. BMAT provides the possibility to translate data from MRI scanners to the BIDS structure, create and manage BIDS datasets as well as develop and run automated processing pipelines. 

## Installation

This section aims at explaining how to download and install BMAT. This software uses a lot of dependencies that needs to be installed which makes the installation process a bit long and tedious. 

### Dependencies

Firstly, this section presents the different dependencies that needs to be installed for this software to work properly. 

#### Python 

This software is written entirely in Python and thus required Python to be installed to work properly. Pip is also needed to install the different packages that the software requires. Pip can sometimes be installed additionnaly when installing Python but not in every case, so it needs to be verified. The installation will be described for the different possible OS.

##### Linux

[Install Python on Linux](https://www.scaler.com/topics/python/install-python-on-linux/)

This link describe extensively how to install python on Linux. 

The easiest solution to install Python is to use the Package Manager. For this, open a terminal a type the following command: 

```
sudo apt-get install python
```

After the installation, you can verify that it all worked properly by typing:

```
python -V
```

This command should show you the vesion of Python. 

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

If there is no error, it is okay. 

The second possibility is to download the installation package directly on the [Python Website](https://www.python.org/downloads/windows/) and install it via the classic installation process. Following this method, pip will not be installed with python. Here are the step to install pip:
1. Download [get-pip.py](https://bootstrap.pypa.io/get-pip.py) script to a folder on your computer. 
2. Open a command prompt in that folder or navigate to that folder
3. Run the script with the following command:

```
python get-pip.py
```

This should install pip. You can check that the installation worked by typing:

```
pip -V
```

##### Mac

Download the installation package directly on the [Python Website](https://www.python.org/downloads/macos/) and install it via the classic installation process. Following this method, pip will not be installed with python. Here are the step to install pip:
1. Download [get-pip.py](https://bootstrap.pypa.io/get-pip.py) script to a folder on your computer. 
2. Open a command prompt in that folder or navigate to that folder
3. Run the script with the following command:

```
python get-pip.py
```

This should install pip. You can check that the installation worked by typing:

```
pip -V
```

#### Docker 

Docker is a set of platform as a service (PaaS) products that use OS-level virtualization to deliver software in packages called containers. The software that hosts the containers is called Docker Engine. BMAT uses docker containers to run analysis pipelines on the medical images. 

[Docker installation tutorial](https://docs.docker.com/get-docker/)

#### ITK-snap

ITK-SNAP is an easy-to-use 3D viewer for medical images (DICOM, NIfTI, etc.) and provide a great framework to perform segmentation of structure. BMAT uses this software to obverse the medical images. 

[ITK-SNAP installation tutorial](http://www.itksnap.org/pmwiki/pmwiki.php?n=Documentation.TutorialSectionInstallation)

### Installation process

#### Download BMAT

Now that all the dependencies have been downloaded and installed, it is now time to install BMAT. The first step is to download the software and you can either:

* If you have git, open a terminal and navigate to the folder you want to install BMAT and then clone this repository by typing: 

```
git clone https://github.com/ColinVDB/BMAT.git
```

* Otherwise, you can download a zip version of the code by clicking on the green Code button at the top right of this page, then **Download ZIP**. Afterwards, extract the Zip file in the folder where you want BMAT to be installed. 

The advantage of installing and using git will be when you will want to update BMAT. You will able to easily do it by typing this command:

```
git pull
```

#### Install python requirements 

After having downloaded BMAT, you need to install all the required python module package in order for the software to work properly. To do so, open a terminal and navigate into the BMAT folder,
```
cd BMAT
```
Then install the required packages using this command:
```
pip install -r requirements.txt
```

#### Install docker required images

The last part of the installation is to pull the different docker images used by the software. For that make sure that the docker daemon socket is active. On Windows and Mac, you will need to run Docker Desktop in the background for it to be active. To pull a docker image, open a terminal and type 'docker pull *name of the image to download*. There is 4 images that needs to be pulled:

1. colinvdb/bmat-ext:0.0.1: this image is an docker extension of BMAT and contains all necessary programs that the software required to work properly like:
    1. dcm2niix: for the conversion from DICOM to NIfTI
    2. ANTs Registration: for the registration pipeline 
    3. Freesurfer: For the automatic segmentation pipeline 
```
docker pull colinvdb/bmat-ext:0.0.1
```
2. bids/validator: this image is used to verify the BIDS validity of the datasets
```
docker pull bids/validator
```
3. blakedewey/phase_unwrap: this image is used to unwrap phase images and is used in th Phase unwrapping pipeline
```
docker pull blakedewey/phase_unwrap
```
4. blakedewey/flairstar: this image is used to compute a FLAIR* image based on a FLAIR and a Magnitude T2* image. 
```
docker pull blakedewey/flairstar:deprecated
```
For this image you will need to change locally the tag of this image by typing:
```
docker tag blakedewey/flairstar:deprecated blakedewey/flairstar:latest
```

**The installation of BMAT is now complete and the software is now ready to be launched**

The next section will show how to use this software

## Utilization

This section aims to explain how to use BMAT. 

### Open/Create new BIDS

When opening the software, a first window pops up and asks to select a BIDS dataset to launch BMAT. The user can either select a folder correponding to a BIDS dataset or create/select an empty folder to create a new BIDS dataset. 

"add picture"

### Main Window 

Here is a picture of the main window of BMAT. It is composed of these different windows:
* Safe File Explorer (left): allows the user to navigate the file that are inside his BIDS dataset
* Dataset Information (top center): contains information about the dataset
* Dataset Actions (top right): buttons to perform Actions on the dataset
* Quick Viewer (bottom right): Quick viewer to observe the file in the dataset in a safe manner
* BIDS menu (top left): contains other other actions to manage the dataset
* Pipelines menu (top left): contains analysis pipelines to process the dataset

"add picture"

### Safe File Explorer

This widget allows the user to navigate the files that are in his dataset in a safe manner, meaning that it prevents the user to unwantingly move and delete files. The user can also open the files in the quick viewer by double-clicking on a file to read the inforation they contain and edit them if wanted. There are also two particularities for specific type of files:
1. NIfTI files (.nii.gz) corresponding to images can be open in the quick viewer by clicking one time on the file; this will show one slice of the image. By double clicking on the file, this will open the image in an ITK-SNAP window, which is a complete 3D viewer for 3D medical images. ITK-SNAP also contains some useful tools for neuroimaging studies; manual segmentation for instance. 
2. The *participants.tsv* file is a file that contains information about the subjects that are in the BIDS dataset. This file contains by default the subject participant_id, age, sex, and MRI session date. However, for neuroimaging studies, it is often useful to have other information on the subject. When opening the *participants.tsv* file in BMAT quick viewer, the software proposes a button **Add** to add information about the subject in this file. Indeed, the software is able to retrieve any information that is contained in the DICOM file. To do so, the user needs to give the software the name of this new information (this will be used for the name of the column), a description of this new information and the DICOM keyword that needs to be used to retrieve this information. The software will then retrieve this information in the DICOM of every subject in the database and keep this new information in the *participants.json* file. It will then automatically retrieve this new information for every new subject added to the dataset.

"add picture"

### BIDS Actions

This section will describe the different features that BMAT integrates to manage a BIDS dataset. 

#### Add Data

When creating a new BIDS dataset, the first thing to do is to import new data in the dataset. BMAT allows the user to import entire MRI session at once instead of sequence one by one. Indeed, when a subject undergoes an MRI exam, he will often be scanned with different MRI sequences. An entire MRI session will contains the DICOM of the different sequences, all taken the same day in series, in a specific folder. 

When clicking on the **Add** button, it will open a dedicated window for the user to select entire sessions of subjects to add to the dataset. The user can add specific folder containing the DICOM files or compressed folder in the ZIP format. Associated with each MRI session, the user can specify a corresponding subject ID and session NUMBER to use; this is especially useful when working with longitudinal study to specify the software that it corresponds to a follow-up MRI session for a certain subject. Otherwise, by not specifying anything, the software will assume that this session corresponds to the first session of a new subject and will select a new available subject ID. By clicking on the **Add to BIDS** button, BMAT will automatically convert the DICOM files into the NIfTI format using *dicom2niix*, create the corresponding folders for this subject in the dataset, rename the files and store them in the right places in the dataset (the DICOM files are stored in the *sourcedata* folder and the NIfTI and json files in the corresponding subject folder. 

"add picture"

For the renaming of the files, BMAT uses a keywords recognition scheme described in the *sequences.csv* file that is found in the *BMAT* folder. This must be completed by the user with information about the sequences that he uses prior to the utilization of the software:
The renaming strategy is user-dependent and based on a mapping between the NIFTI file name after conversion with *dicom2niix* (mainly the *SeriesDescription* in the DICOM files) and the corresponding BIDS modality, described in the *sequences.csv* file. The mapping file needs only to be completed once at the beginning of the study and the software will then be able to recognize and work with these sequences. The mapping file works as follow; the software recognizes keywords in the file name and maps them to the corresponding BIDS name. The renaming scheme works in 3 steps: 
1. The software finds the modality of a sequence by trying one by one the different possible keyword(s) (one or several separated by ‘+’) in the modality column of the file and maps the matching keywords to the corresponding BIDS modality in the ‘modality_bids’ column.
2. Once the modality has been found, the software will check if other BIDS field needs to be completed by using a similar scheme on the modality sub table. It checks if a keyword from a BIDS field column (e.g. ‘acq’) lies in the filename and uses the corresponding BIDS label (in ‘acq_bids’ column) for the renaming. The user can add columns to the file corresponding to other BIDS field; one column named after the BIDS field with the specific keywords and the other with the ‘_bids’ extension that contains the corresponding label to use. An empty cell is not taken into account while a ‘_’ cell is always taken into account.
3. Finally, the MRI_type column contains the name of the subfolder in which this sequence needs to be stored. If the *IGNORED* keyword is used, the sequence will not be considered in the BIDS dataset. This is especially useful to not consired the Localization sequence that are used during the MRI exam to acquire the other sequences. 
The software is always trying the keywords from top to bottom of the file and stop as soon as it gets a match. This scheme means that it is up to the user to follow BIDS specification for the renaming of the sequences. The software will only validate the dataset as BIDS compliant or not. 

"add picture"

#### Remove Data

This options allows the user to remove entire subject or session from the dataset. BMAT will automatically remove all the data corresponding to this subject or session from the dataset. It will also asks the user he want to delete the DICOM of this subject of the *sourcedata* folder. If not the DICOM will me moved to a dedicated folder in the *sourcedata* folder. 

#### Rename subject/session/sequence

This feeature allows the user to rename subject session or sequence in the dataset. When renaming a sequence, BMAT will automatically rename the sequence for all the subjetcs inside the dataset. 

### BIDS Menu

This menu contains some more features to manage the BIDS dataset. Here is a description of the different features:
* Create BIDS directory: this will open a similar window the the first one for the user to create a new empty folder to select and create a new empty BIDS dataset.
* Change BIDS directory: this will open a similar window the the first one for the user to select a new folder corresponding to a new BIDS dataset.
* BIDS Quality Control: this will run a *bids-validator* program that will give the user informations about the validity of his BIDS dataset according to the BIDS specifications as well as give a link towards the BIDS specifications
* Update Authors: allows the user to update the name of the authors of the BIDS dataset. 

### Pipelines Menu

#### Available pipelines

##### Registration pipeline

##### FLAIR* pipeline

##### Phase unwrapping pipeline

##### LesVolLoc pipeline
:warning: <span style="color:red">some **This Pipeline is not functionnal yet !!!** text</span> :warning:

#### Adding pipelines


