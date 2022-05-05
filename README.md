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

## Utilization


