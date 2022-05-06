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


