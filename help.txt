========================================================================================================
PRIZM-RTSA (Real Time Spectrum Analyser) - This repository contains the necessary scripts to collect 
the 'scio'(pol0 & pol1) files from a snapboard and to display the data on an interactive user interface.
========================================================================================================
____________________________________________________________________________________________________
The following dependencies are required in order to the code: python, matplotlib, pyside, numpy, qt4
____________________________________________________________________________________________________

Install Python 2.7
---------------------
- sudo apt-get install python

Install Matplotlib
---------------------
- sudo apt-get install python-matplotlib

Install Numpy
----------------
- sudo apt-get install python-numpy

Install Qt4
--------------
- sudo apt-get install python-qt4

Install Pyside
-----------------
- sudo apt-get install python-pyside

Create a SSH_RSA KEY pair
-------------------------
On your terminal run the following commands. Replace 'user@ip-address' with the one for the Raspberry Pi e.g. pi@255.255.255.255
- ssh-keygen
- ssh-copy-id -i ~/.ssh/id_rsa.pub user@ip-address
(the next line is optional and just to ensure that a password is not required anymore)
- ssh user@ip-address

Run the main script
-------------------
Once the snapboard has started capturing the spectra. 
Run the following commands on a terminal in the cloned folder in the following sequence.

(the first command only needs to be executed once after cloning the repository)
- chmod +x *.sh
- ./run.sh

Areas of UI improvements
------------------------
The following points represent areas where the software and usability of the spectrum analyser can be improved.
- Adding a help menu in the UI with the descriptions on the interfaces
- Showing short descriptions on the interfaces when the mouse hovers over
