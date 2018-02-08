# SpectrogramUI.py
# Code adapted from Tony DiCola (ton@dicola.com) - http://www.github.com/tdicola/

# User interface for Spectrogram program.
from __future__ import division
import os
import matplotlib
import scio
import time
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4']='PySide'
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.cm import get_cmap
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.ticker import MultipleLocator, FuncFormatter, FormatStrFormatter
from matplotlib import dates
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from PySide import QtCore, QtGui

VERSION = 'PRIZM Spectrogram'


def is_non_zero_file(fpath):  #Check if file exists and is not empty
    return os.path.isfile(fpath) and os.path.getsize(fpath) > 0

# Add global version number/name
global 	sampleTimeValue,timeRegionValue,spectrumNumberScale,slidersHaveBeenChanged,horizontalslidersHaveBeenChanged,\
maximumTime, displayAverage, spectrumCounter, isLocked, sampleTimeValue, displayAverage_pol1, \
timeRegionValue_pol1,spectrumNumberScale_pol1,slidersHaveBeenChanged_pol1,horizontalslidersHaveBeenChanged_pol1,\
pol0_has_been_initialised, pol1_has_been_initialised, lockedPlotEvent, cwd, snapboard_capture_time


cwd = os.getcwd()	#Current working directory

#These global variables are used to keep track of the interface states
pol0_has_been_initialised = False
pol1_has_been_initialised = False
isLocked = False
lockedPlotEvent = 0
spectrumCounter=0
snapboard_capture_time=3.3	#	#The 'snapboard_capture_time' value represents the average number of seconds taken to acquire the data SnapBoard.
								#You may change this to suit the time taken on your system
#Pol 0
sampleTimeValue=5
timeRegionValue=0
spectrumNumberScale=0
slidersHaveBeenChanged=False
horizontalslidersHaveBeenChanged=False
displayAverage=False
#Pol 1
sampleTimeValue_pol1=5
timeRegionValue_pol1=0
spectrumNumberScale_pol1=0
slidersHaveBeenChanged_pol1=False
horizontalslidersHaveBeenChanged_pol1=False
displayAverage_pol1=False

#This is the default maximum buffer time (it corresponds to a day)
maximumTime = 86400

class SpectrogramCanvas(FigureCanvas):
	def __init__(self, window):
		global pol0_has_been_initialised, pol1_has_been_initialised
		"""Initialize spectrogram canvas graphs."""
		# Tell numpy to ignore errors like taking the log of 0
		np.seterr(all='ignore')

		# Set up figure to hold plots
		self.figure = Figure(figsize=(1024,768), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0))

		# Initialize canvas
		super(SpectrogramCanvas, self).__init__(self.figure)

		gs = GridSpec(1, 2, left=0.07, right=0.95, bottom=0.06, top=0.95, wspace=0.05)
		#gs.tight_layout(self.figure)
		gs0 = GridSpecFromSubplotSpec(2, 2, subplot_spec=gs[0], height_ratios=[1,2], width_ratios=[9.5, 0.5])
		gs1 = GridSpecFromSubplotSpec(2, 2, subplot_spec=gs[1], height_ratios=[1,2], width_ratios=[9.5, 0.5])

		# Set up spectrogram waterfall plot
		self.spectAxPol0 = self.figure.add_subplot(gs0[2])
		self.spectAxPol0.set_title('Spectrogram - Pol 0')
		self.spectAxPol0.set_ylabel('Sample Age (seconds)')
		self.spectAxPol0.set_xlabel('Frequency Bin (MHz)')
		self.spectAxPol0.set_xlim(left=0, right=250)
		self.spectPlotPol0 = self.spectAxPol0.imshow(([],[]), aspect='auto', cmap=get_cmap('jet')) #Create empty waterfall plot variable

		# Set up frequency histogram bar plot
		self.histAxPol0 = self.figure.add_subplot(gs0[0])
		self.histAxPol0.set_title('Frequency Spectrum - Pol 0')
		self.histAxPol0.set_ylabel('Intensity (dB)')
		self.histAxPol0.set_xlim(left=0, right=250)
		self.histPlotPol0, = self.histAxPol0.plot([],[]) #Create empty spectrogram plot variable

		# Set up spectrogram waterfall plot
		self.spectAxPol1 = self.figure.add_subplot(gs1[2])
		self.spectAxPol1.set_title('Spectrogram - Pol 1')
		self.spectAxPol1.set_ylabel('Sample Age (seconds)')
		self.spectAxPol1.set_xlabel('Frequency Bin (MHz)')
		self.spectAxPol1.set_xlim(left=0, right=250)
		self.spectPlotPol1 = self.spectAxPol1.imshow(([],[]), aspect='auto', cmap=get_cmap('jet')) #Create empty waterfall plot variable

		# Set up frequency histogram bar plot
		self.histAxPol1 = self.figure.add_subplot(gs1[0])
		self.histAxPol1.set_title('Frequency Spectrum - Pol 1')
		self.histAxPol1.set_ylabel('Intensity (dB)')
		self.histAxPol1.set_xlim(left=0, right=250)
		self.histPlotPol1, = self.histAxPol1.plot([],[]) #Create empty spectrogram plot variable

		# Set up spectrogram color bar for the waterfall plot
		self.colourBarPol1 = self.figure.add_subplot(gs1[3])
		self.figure.colorbar(self.spectPlotPol1, cax=self.colourBarPol1, use_gridspec=True, format=FuncFormatter(lambda x, pos: '%d' % (x*100.0)))
		self.colourBarPol1.set_ylabel('Intensity')

		msg = QtGui.QMessageBox()
		msg.setIcon(QtGui.QMessageBox.Critical)
		msg.setWindowTitle("SCIO Files Missing")
		msg.setStandardButtons(QtGui.QMessageBox.Ok)
		#Show a message of which files are missing if files are missing
		if not is_non_zero_file('%s/pol0.scio' % cwd) and not is_non_zero_file('%s/pol1.scio' % cwd):
			msg.setText("Both pol0.scio and pol1.scio are missing. The interface will be enabled when the files are retrieved.")
			msg.exec_()
		if is_non_zero_file('%s/pol0.scio' % cwd) and not is_non_zero_file('%s/pol1.scio' % cwd):
			msg.setText("'pol1.scio' is missing.")
			msg.exec_()
		if not is_non_zero_file('%s/pol0.scio' % cwd) and is_non_zero_file('%s/pol1.scio' % cwd):
			msg.setText("'pol0.scio' is missing.")
			msg.exec_()


		#Get limits of the waterfall plot; these variable are used when zooming into the subplot
		#Pol0
		self.ymin, self.ymax = self.spectAxPol0.get_ylim()
		#Pol1
		self.ymin_pol1, self.ymax_pol1 = self.spectAxPol1.get_ylim()

		#Initiliase variables
		#Pol0
		self.horizontalMarker = 0	#This is the variable that stores the height of the spectrum marker on the interface (black dashed line)
		self.spectrumMarker = 0		#This is the variable that stores the spectrum number in the array
		self.maxExtentStretch = 60	#This is the maximum height to which the waterfall plot is stretched to
		#Pol1
		self.horizontalMarker_pol1 = 0	#This is the variable that stores the height of the spectrum marker on the interface (black dashed line)
		self.spectrumMarker_pol1 = 0	#This is the variable that stores the spectrum number in the array
		self.maxExtentStretch_pol1 = 60	#This is the maximum height to which the waterfall plot is stretched to

		#Initialize pol0
		#Pol0
		self.init_num_rows = 0
		self.init_num_cols = 0
		#Pol1
		self.init_num_rows_pol1 = 0
		self.init_num_cols_pol1 = 0

		#Functions that run in the background
		self.ani = FuncAnimation(self.figure, self._update, interval=2000, blit=False)
		self.updateAni = FuncAnimation(self.figure, self._updateAxis, interval=100, blit=False)


	def initializePol0(self, *fargs):
		#Reset graphs
		self.spectAxPol0.cla()
		self.histAxPol0.cla()

		#Setup spectrum graph
		self.histAxPol0.set_title('Frequency Spectrum - Pol 0')
		self.histAxPol0.set_ylabel('Intensity (dB)')
		self.histAxPol0.set_xlim(left=0, right=250)
		self.histAxPol0.callbacks.connect('xlim_changed', self.spectPol0XlimUpdate)	#Setup lock feature in pan and zoom

		#Setup waterfall graph
		self.spectAxPol0.set_title('Spectrogram - Pol 0')
		self.spectAxPol0.set_ylabel('Sample Age (seconds)')
		self.spectAxPol0.set_xlabel('Frequency Bin (MHz)')
		self.spectAxPol0.set_xlim(left=0, right=250)
		self.spectAxPol0.callbacks.connect('xlim_changed', self.histPol0XlimUpdate)	#Setup lock feature in pan and zoom


		#read the correct file by giving the right path
		self.pol0 = scio.read('%s/pol0.scio' % cwd)
		self.num_rows, self.num_cols = np.shape(self.pol0)

		#define the x-axis to span 0--250 MHz
		self.frequency = np.linspace(0,250,4096)

		#Setup waterfall plot
		self.init_num_rows, self.init_num_cols = np.shape(self.pol0)
		self.waterfall = np.log10(np.abs(self.pol0))
		self.median = np.median(self.waterfall)
		self.std = np.std(self.waterfall)
		self.vmin , self.vmax = (self.median-self.std) , (self.median+self.std)
		self.nu=((np.arange(self.waterfall.shape[1])+0.5)/(1.0*self.waterfall.shape[1]))*250; # frequency range in MHz
		self.spectPlotPol0 = self.spectAxPol0.imshow(self.waterfall, aspect='auto', cmap='jet',extent=[0,250,24,0],vmin=self.vmin,vmax=self.vmax)

		self.maxExtentStretch = self.init_num_rows*snapboard_capture_time	#This equation pulls all the initial data from the 'scio' and gets the time exceeded by multiplying the number of spectra with snapboard_capture_time

		self.spectPlotPol0.set_extent([0,250,self.maxExtentStretch,0])
		self.spectAxPol0.set_ylim(top=timeRegionValue, bottom=timeRegionValue+sampleTimeValue)

		self.ymin, self.ymax = self.spectAxPol0.get_ylim()

		#Save plotting data
		self.data = self.pol0[self.init_num_rows-self.horizontalMarker-1,:]

		#take a mean along the rows
		self.average_data = np.mean(self.pol0, axis = 0)
		histData = np.log(self.data)
		histData_dB = 10*np.log10(2**histData)
		self.histPlotPol0, = self.histAxPol0.plot(self.frequency,histData_dB)



	def initializePol1(self, *fargs):
		#Reset graphs
		self.spectAxPol1.cla()
		self.histAxPol1.cla()
		self.colourBarPol1.cla()

		#Setup spectrum graph
		self.histAxPol1.set_title('Frequency Spectrum - Pol 1')
		self.histAxPol1.set_ylabel('Intensity (dB)')
		self.histAxPol1.set_xlim(left=0, right=250)
		self.histAxPol1.callbacks.connect('xlim_changed', self.spectPol1XlimUpdate)	#Setup lock feature in pan and zoom

		#Setup waterfall graph
		self.spectAxPol1.set_title('Spectrogram - Pol 1')
		self.spectAxPol1.set_ylabel('Sample Age (seconds)')
		self.spectAxPol1.set_xlabel('Frequency Bin (MHz)')
		self.spectAxPol1.set_xlim(left=0, right=250)
		self.spectAxPol1.callbacks.connect('xlim_changed', self.histPol1XlimUpdate)	#Setup lock feature in pan and zoom


		#read the correct file by giving the right path
		self.pol1 = scio.read('%s/pol1.scio' % cwd)
		self.num_rows_pol1, self.num_cols_pol1 = np.shape(self.pol1)

		#define the x-axis to span 0--250 MHz
		self.frequency_pol1 = np.linspace(0,250,4096)

		#Setup waterfall plot
		self.init_num_rows_pol1, self.init_num_cols_pol1 = np.shape(self.pol1)
		self.waterfall_pol1 = np.log10(np.abs(self.pol1))
		self.median_pol1 = np.median(self.waterfall_pol1)
		self.std_pol1 = np.std(self.waterfall_pol1)
		self.vmin_pol1 , self.vmax_pol1 = (self.median_pol1-self.std_pol1) , (self.median_pol1+self.std_pol1)
		self.nu_pol1=((np.arange(self.waterfall_pol1.shape[1])+0.5)/(1.0*self.waterfall_pol1.shape[1]))*250; # frequency range in MHz
		self.spectPlotPol1 = self.spectAxPol1.imshow(self.waterfall_pol1, aspect='auto', cmap='jet',extent=[0,250,24,0],vmin=self.vmin_pol1,vmax=self.vmax_pol1)

		#Recreate the colorbar to match the data
		self.figure.colorbar(self.spectPlotPol1, cax=self.colourBarPol1, use_gridspec=True, format=FuncFormatter(lambda x, pos: '%d' % (x*100.0)))
		self.colourBarPol1.set_ylabel('Intensity')

		self.maxExtentStretch_pol1 = self.init_num_rows_pol1*snapboard_capture_time
		self.spectPlotPol1.set_extent([0,250,self.maxExtentStretch_pol1,0])
		self.spectAxPol1.set_ylim(top=timeRegionValue_pol1, bottom=timeRegionValue_pol1+sampleTimeValue_pol1)

		self.ymin_pol1, self.ymax_pol1 = self.spectAxPol1.get_ylim()

		#Save plotting data
		self.data_pol1 = self.pol1[self.init_num_rows_pol1-self.horizontalMarker_pol1-1,:]

		#take a mean along the rows
		self.average_data_pol1 = np.mean(self.pol1, axis = 0)
		histData = np.log(self.data_pol1)
		histData_dB = 10*np.log10(2**histData)
		self.histPlotPol1, = self.histAxPol1.plot(self.frequency_pol1,histData_dB)

	#Pol 0 - Update limits to spectrogram
	def histPol0XlimUpdate(self, *fargs):
		global lockedPlotEvent
		if isLocked:
			if lockedPlotEvent == 0:
				lockedPlotEvent = 1
				self.histAxPol0.set_xlim(self.spectAxPol0.get_xlim())
			else:
				lockedPlotEvent = 0

	#Pol 1 - Update limits to spectrogram
	def histPol1XlimUpdate(self, *fargs):
		global lockedPlotEvent
		if isLocked:
			if lockedPlotEvent == 0:
				lockedPlotEvent = 1
				self.histAxPol1.set_xlim(self.spectAxPol1.get_xlim())
			else:
				lockedPlotEvent = 0

	#Pol 0 - Update limits to frequency spectrum
	def spectPol0XlimUpdate(self, *fargs):
		global lockedPlotEvent
		if isLocked:
			if lockedPlotEvent == 0:
				lockedPlotEvent = 1
				self.spectAxPol0.set_xlim(self.histAxPol0.get_xlim())
			else:
				lockedPlotEvent = 0

	#Pol 1 - Update limits to frequency spectrum
	def spectPol1XlimUpdate(self, *fargs):
		global lockedPlotEvent
		if isLocked:
			if lockedPlotEvent == 0:
				lockedPlotEvent = 1
				self.spectAxPol1.set_xlim(self.histAxPol1.get_xlim())
			else:
				lockedPlotEvent = 0


	def _update(self, *fargs):
		global displayAverage, spectrumCounter, pol0_has_been_initialised, pol1_has_been_initialised, displayAverage_pol1

		if is_non_zero_file('%s/pol0.scio' % cwd):
			#Initialize spectrum plots if not done before
			if not pol0_has_been_initialised:
				self.initializePol0()
				#This is the marker which spreads across the graphs
				self.hline = self.spectAxPol0.axhline(self.horizontalMarker, color='k', linestyle='--', linewidth=2) #Pol 0
				pol0_has_been_initialised = True

			#read the correct file by giving the right path
			arrayTemp = scio.read('%s/pol0.scio' % cwd)
			self.num_rows, self.num_cols = np.shape(arrayTemp)

			if self.init_num_rows != self.num_rows:	#Check if the number of rows has changed implying a new spectrum is present
				try:
					self.pol0 = np.vstack([arrayTemp[spectrumCounter],self.pol0])
				except IndexError:	#Else the new number of spectrum is smaller than the previous because a new file is created ('scio' file has changed folders in the snapboard)
					spectrumCounter=0
					self.pol0 = np.vstack([arrayTemp[spectrumCounter],self.pol0])

				self.init_num_rows = self.num_rows	#Update number of rows

				self.num_rows, self.num_cols = np.shape(self.pol0)
				self.waterfall = np.log10(np.abs(self.pol0))
				self.median = np.median(self.waterfall)
				self.std = np.std(self.waterfall)
				self.vmin , self.vmax = (self.median-self.std) , (self.median+self.std)
				self.nu=((np.arange(self.waterfall.shape[1])+0.5)/(1.0*self.waterfall.shape[1]))*250; # frequency range in MHz
				self.spectPlotPol0.set_data(self.waterfall)

				self._extendYaxis(snapboard_capture_time, 'pol0')

				#Update spectrum according to the states of the interface
				if displayAverage:
					extentValue = self.spectPlotPol0.get_extent()
					[top, bottom] = self.spectAxPol0.get_ylim()
					if(extentValue[2] < top):	#If the end of the waterfall is visible, set the top to the end of the spectrum
						top = np.rint(extentValue[2])
					bottom = np.rint(bottom/snapboard_capture_time)	#Scale back for array indexing
					top = np.rint(top/snapboard_capture_time)	#Scale back for array indexing
					self.average_data = np.mean(self.pol0[bottom:(top+1),:], axis = 0)	#Get average spectrum of data displayed on the waterfall plot
					histData = np.log(self.average_data)
					histData_dB = 10*np.log10(2**histData)
					self.histPlotPol0.set_ydata(histData_dB)
				else:
					self.horizontalMarker = spectrumNumberScale	#Get value from the UI slider
					self.spectrumMarker = self.horizontalMarker/snapboard_capture_time	#Scale down by 'snapboard_capture_time' for array indexing
					self.hline.set_ydata(self.horizontalMarker)	#Set black marker at location
					spectrumMarkerRounded = np.rint(self.spectrumMarker)
					try:
						self.data = self.pol0[spectrumMarkerRounded]
					except IndexError:
						self.data = self.pol0[0]
					histData = np.log(self.data)
					histData_dB = 10*np.log10(2**histData)
					self.histPlotPol0.set_ydata(histData_dB)

		if is_non_zero_file('%s/pol1.scio' % cwd):
			#Initialize spectrum plots if not done before
			if not pol1_has_been_initialised:
				self.initializePol1()
				#This is the marker which spreads across the graphs
				self.hline_pol1 = self.spectAxPol1.axhline(self.horizontalMarker_pol1, color='k', linestyle='--', linewidth=2) #Pol 1
				pol1_has_been_initialised = True

			#read the correct file by giving the right path
			arrayTemp = scio.read('%s/pol1.scio' % cwd)
			self.num_rows_pol1, self.num_cols_pol1 = np.shape(arrayTemp)

			if self.init_num_rows_pol1 != self.num_rows_pol1:	#Check if the number of rows has changed implying a new spectrum is present
				try:
					self.pol1 = np.vstack([arrayTemp[spectrumCounter],self.pol1])
				except IndexError:	#Else the new number of spectrum is smaller than the previous because a new file is created ('scio' file has changed folders in the snapboard)
					spectrumCounter=0
					self.pol1 = np.vstack([arrayTemp[spectrumCounter],self.pol1])

				self.init_num_rows_pol1 = self.num_rows_pol1	#Update number of rows

				self.num_rows_pol1, self.num_cols_pol1 = np.shape(self.pol1)
				self.waterfall_pol1 = np.log10(np.abs(self.pol1))
				self.median_pol1 = np.median(self.waterfall_pol1)
				self.std_pol1 = np.std(self.waterfall_pol1)
				self.vmin_pol1 , self.vmax_pol1 = (self.median_pol1-self.std_pol1) , (self.median_pol1+self.std_pol1)
				self.nu_pol1=((np.arange(self.waterfall_pol1.shape[1])+0.5)/(1.0*self.waterfall_pol1.shape[1]))*250; # frequency range in MHz
				self.spectPlotPol1.set_data(self.waterfall_pol1)

				self._extendYaxis(snapboard_capture_time, 'pol1')

				#Update spectrum according to the states of the interface
				if displayAverage_pol1:
					extentValue = self.spectPlotPol1.get_extent()
					[top, bottom] = self.spectAxPol1.get_ylim()
					if(extentValue[2] < top):	#If the end of the waterfall is visible, set the top to the end of the spectrum
						top = np.rint(extentValue[2])
					bottom = np.rint(bottom/snapboard_capture_time)	#Scale back for array indexing
					top = np.rint(top/snapboard_capture_time)	#Scale back for array indexing
					self.average_data_pol1 = np.mean(self.pol1[bottom:(top+1),:], axis = 0)	#Get average spectrum of data displayed on the waterfall plot
					histData = np.log(self.average_data_pol1)
					histData_dB = 10*np.log10(2**histData)
					self.histPlotPol1.set_ydata(histData_dB)
				else:
					self.horizontalMarker_pol1 = spectrumNumberScale_pol1	#Get value from the UI slider
					self.spectrumMarker_pol1 = self.horizontalMarker_pol1/snapboard_capture_time	#Scale down by 'snapboard_capture_time' for array indexing
					self.hline_pol1.set_ydata(self.horizontalMarker_pol1)	#Set black marker at location
					spectrumMarkerRounded = np.rint(self.spectrumMarker_pol1)
					try:
						self.data_pol1 = self.pol1[spectrumMarkerRounded]
					except IndexError:
						self.data_pol1 = self.pol1[0]
					histData = np.log(self.data_pol1)
					histData_dB = 10*np.log10(2**histData)
					self.histPlotPol1.set_ydata(histData_dB)

		spectrumCounter = spectrumCounter + 1	#Move to the next spectrum

		return (self.histPlotPol0, self.spectPlotPol0, self.histPlotPol1, self.spectPlotPol1)




	def _updateAxis(self, *fargs):
		global slidersHaveBeenChanged, horizontalslidersHaveBeenChanged, maximumTime,displayAverage,\
		slidersHaveBeenChanged_pol1, horizontalslidersHaveBeenChanged_pol1,displayAverage_pol1
		#Pol 0
		if slidersHaveBeenChanged:
			self.spectPlotPol0.set_data(self.waterfall)	#Update frequency spectrum to display 'average' spectra or selected spectra
			slidersHaveBeenChanged=False
		if horizontalslidersHaveBeenChanged and not displayAverage:
			self.horizontalMarker = spectrumNumberScale	#Get value from UI slider
			self.spectrumMarker = (self.horizontalMarker/(self.num_rows*snapboard_capture_time))*(self.num_rows-1)	#Scale the UI slider to the index of the array in pol0
			spectrumMarkerRounded = np.rint(self.spectrumMarker)
			self.hline.set_ydata(self.horizontalMarker)
			try:
				self.data = self.pol0[spectrumMarkerRounded]
			except IndexError:
				self.data = self.pol0[0]
			histData = np.log(self.data)
			histData_dB = 10*np.log10(2**histData)
			self.histPlotPol0.set_ydata(histData_dB)
			horizontalslidersHaveBeenChanged = False
		#Pol 1
		if slidersHaveBeenChanged_pol1:
			self.spectPlotPol1.set_data(self.waterfall_pol1)	#Update frequency spectrum to display 'average' spectra or selected spectra
			slidersHaveBeenChanged_pol1=False
		if horizontalslidersHaveBeenChanged_pol1 and not displayAverage_pol1:
			self.horizontalMarker_pol1 = spectrumNumberScale_pol1	#Get value from UI slider
			self.spectrumMarker_pol1 = (self.horizontalMarker_pol1/(self.num_rows_pol1*snapboard_capture_time))*(self.num_rows_pol1-1)	#Scale the UI slider to the index of the array in pol1
			spectrumMarkerRounded_pol1 = np.rint(self.spectrumMarker_pol1)
			self.hline_pol1.set_ydata(self.horizontalMarker_pol1)
			try:
				self.data_pol1 = self.pol1[spectrumMarkerRounded_pol1]
			except IndexError:
				self.data_pol1 = self.pol1[0]
			histData = np.log(self.data_pol1)
			histData_dB = 10*np.log10(2**histData)
			self.histPlotPol1.set_ydata(histData_dB)
			horizontalslidersHaveBeenChanged_pol1 = False



	def updateCaptureRange(self, pol):
		"""Adjust low and high intensity limits for histogram and spectrum axes."""
		if pol=='pol0':
			#Convert values to time format
			daysZoom = sampleTimeValue//86399
			hoursZoom = sampleTimeValue//3599
			minutesZoom = sampleTimeValue//59
			daysScroll = timeRegionValue//86399
			hoursScroll = timeRegionValue//3599
			minutesScroll = timeRegionValue//59

			self.spectAxPol0.set_ylim(top=timeRegionValue, bottom=timeRegionValue+sampleTimeValue)	#Update waterfall limits according to UI values
			self.ymin, self.ymax = self.spectAxPol0.get_ylim()	#Update min and max values

			#Display numbers in time format
			if (daysZoom or daysScroll) == 0:
				if (hoursZoom or hoursScroll) == 0:
					if (minutesZoom or minutesScroll) == 0:
						self.spectAxPol0.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%d' % (x*1)))
					else:
						self.spectAxPol0.set_ylabel('Sample Age (minutes:seconds)')
						self.spectAxPol0.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%s' %(time.strftime("%M:%S", time.gmtime(x)))))
				else:
					self.spectAxPol0.set_ylabel('Sample Age (hours:minutes)')
					self.spectAxPol0.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%s' %(time.strftime("%H:%M", time.gmtime(x)))))
			else:
				self.spectAxPol0.set_ylabel('Sample Age (days-hour)')
				self.spectAxPol0.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%s' %('Day '+str(int(time.strftime("%d", time.gmtime(x)))-1)+(time.strftime("-%H:%M", time.gmtime(x))))))

		if pol=='pol1':
			#Convert values to time format
			daysZoom = sampleTimeValue_pol1//86399
			hoursZoom = sampleTimeValue_pol1//3599
			minutesZoom = sampleTimeValue_pol1//59
			daysScroll = timeRegionValue_pol1//86399
			hoursScroll = timeRegionValue_pol1//3599
			minutesScroll = timeRegionValue_pol1//59

			self.spectAxPol1.set_ylim(top=timeRegionValue_pol1, bottom=timeRegionValue_pol1+sampleTimeValue_pol1)	#Update waterfall limits according to UI values
			self.ymin_pol1, self.ymax_pol1 = self.spectAxPol1.get_ylim()	#Update min and max values

			#Display numbers in time format
			if (daysZoom or daysScroll) == 0:
				if (hoursZoom or hoursScroll) == 0:
					if (minutesZoom or minutesScroll) == 0:
						self.spectAxPol1.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%d' % (x*1)))
					else:
						self.spectAxPol1.set_ylabel('Sample Age (minutes:seconds)')
						self.spectAxPol1.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%s' %(time.strftime("%M:%S", time.gmtime(x)))))
				else:
					self.spectAxPol1.set_ylabel('Sample Age (hours:minutes)')
					self.spectAxPol1.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%s' %(time.strftime("%H:%M", time.gmtime(x)))))
			else:
				self.spectAxPol1.set_ylabel('Sample Age (days-hour)')
				self.spectAxPol1.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%s' %('Day '+str(int(time.strftime("%d", time.gmtime(x)))-1)+(time.strftime("-%H:%M", time.gmtime(x))))))



	def _extendYaxis(self, value, pol):
		if pol=='pol0':
			extended = self.spectPlotPol0.get_extent()
			extended = extended[2]+value	#Get the bottom value where the data is squeezed
			if extended <= (maximumTime+snapboard_capture_time):	#If end of the spectrum is visible, stretch the data to the end of the spectrum and not the bottom of the axes
				self.spectPlotPol0.set_extent([0,250,extended,0])
			else:
				excessRows = int((extended - maximumTime)//snapboard_capture_time) #Number of rows outside the buffer time
				self.pol0 = np.delete(self.pol0, slice(self.num_rows-excessRows,self.num_rows), axis=0) #Delete the array variables outside the buffer time
				if (excessRows > 1):
					self.spectPlotPol0.set_extent([0,250,extended-snapboard_capture_time*excessRows,0])
		if pol=='pol1':
			extended = self.spectPlotPol1.get_extent()
			extended = extended[2]+value	#Get the bottom value where the data is squeezed
			if extended <= (maximumTime+snapboard_capture_time):	#If end of the spectrum is visible, stretch the data to the end of the spectrum and not the bottom of the axes
				self.spectPlotPol1.set_extent([0,250,extended,0])
			else:
				excessRows = int((extended - maximumTime)//snapboard_capture_time) #Number of rows outside the buffer time
				self.pol1 = np.delete(self.pol1, slice(self.num_rows_pol1-excessRows,self.num_rows_pol1), axis=0)	#Delete the array variables outside the buffer time
				if (excessRows > 1):
					self.spectPlotPol1.set_extent([0,250,extended-snapboard_capture_time*excessRows,0])




class MainWindow(QtGui.QMainWindow):
	def __init__(self):
		"""Set up the main window. This is the GUI components"""
		super(MainWindow, self).__init__()
		self.openDevice = None
		main = QtGui.QWidget()
		self.UI_Layout = self._setupMainLayout()
		main.setLayout(self.UI_Layout)
		self.enable = FuncAnimation(self.spectrogram.figure, self._enableUI, interval=500, blit=False)
		self.setCentralWidget(main)
		self.status = self.statusBar()
		self.setGeometry(10,10,900,600)
		self.setWindowTitle('PRIZM 100MHz Antenna')
		self.show()

	def updateStatus(self, message=''):
		"""Update the status bar of the widnow with the provided message text."""
		self.status.showMessage(message)

	def _setupMainLayout(self):
		global maximumTime
		self.controls = QtGui.QVBoxLayout()
		self.bufferControl = QtGui.QGroupBox('Total Time Buffer')
		self.bufferControl.setLayout(QtGui.QHBoxLayout())
		self.navigationControl = QtGui.QGroupBox()
		self.navigationControl.setLayout(QtGui.QHBoxLayout())

		self.spinBoxHour = QtGui.QSpinBox(value=0)
		self.spinBoxMinute = QtGui.QSpinBox(value=0)
		self.spinBoxDay = QtGui.QSpinBox(value=1)
		self.spinBoxDay.setRange(0,365)
		self.spinBoxMinute.setRange(0,59)
		self.spinBoxHour.setRange(0,23)
		self.spinBoxDay.valueChanged.connect(self.setMaximumTime)
		self.spinBoxMinute.valueChanged.connect(self.setMaximumTime)
		self.spinBoxHour.valueChanged.connect(self.setMaximumTime)

		self.bufferControl.layout().addWidget(QtGui.QLabel('Days:'), 1)
		self.bufferControl.layout().addWidget(self.spinBoxDay, 1)
		self.bufferControl.layout().addWidget(QtGui.QLabel('Hours:'), 1)
		self.bufferControl.layout().addWidget(self.spinBoxHour, 1)
		self.bufferControl.layout().addWidget(QtGui.QLabel('Minutes:'), 1)
		self.bufferControl.layout().addWidget(self.spinBoxMinute, 1)

		maximumTime = (86400*self.spinBoxDay.value()) + (3600*self.spinBoxHour.value()) + (60*self.spinBoxMinute.value())

		self.spectrogram = SpectrogramCanvas(self)
		self.navLocked = QtGui.QCheckBox("Lock Plot")
		self.navLocked.setChecked(False)
		self.navLocked.toggled.connect(self.Lockedcheckbox_toggled)

		#Set Navigation bar
		self.toolbar = NavigationToolbar(self.spectrogram, self)
		self.navigationControl.layout().addWidget(self.toolbar)
		self.navigationControl.layout().addWidget(self.navLocked)
		self.controls.addWidget(self.navigationControl)
		self.controls.addWidget(self.bufferControl)

		self.polController = self._setupControls()
		self.controls.addWidget(self.polController)

		self.calibrateBtn = QtGui.QPushButton('Calibrate Waterfall Spectrums of Pol 0 and Pol 1')
		self.calibrateBtn.clicked.connect(self._calibrateBtn)
		self.clearBtn = QtGui.QPushButton('Clear Waterfall Spectrums of Pol 0 and Pol 1')
		self.clearBtn.clicked.connect(self._clearBtn)

		self.controls.addWidget(self.calibrateBtn)
		self.controls.addWidget(self.clearBtn)
		self.controls.addStretch(1)

		layout = QtGui.QHBoxLayout()
		layout.addLayout(self.controls)
		layout.addWidget(self.spectrogram)


		if not (pol0_has_been_initialised or pol1_has_been_initialised):	#If any of the 'scio' files are missing disable the UI
			self.bufferControl.setEnabled(False)
			self.polController.setEnabled(False)
			self.navigationControl.setEnabled(False)
			self.calibrateBtn.setEnabled(False)
			self.clearBtn.setEnabled(False)
		return layout

	def _enableUI(self, value):
		if pol0_has_been_initialised and pol1_has_been_initialised:	#Enable the UI when the 'scio' files are present
			try:
				self.bufferControl.setEnabled(True)
				self.polController.setEnabled(True)
				self.navigationControl.setEnabled(True)
				self.calibrateBtn.setEnabled(True)
				self.clearBtn.setEnabled(True)
				self.enable.event_source.stop()
			except AttributeError:
				pass

	def _setupControls(self):
		global maximumTime, slidersHaveBeenChanged, pol0_has_been_initialised, pol1_has_been_initialised

		#Pol 0
		ZoomSlider = QtGui.QSlider(QtCore.Qt.Orientation.Horizontal)	#Used to zoom into the region where the spectrum is being examined - Pol 0
		ScrollSlider = QtGui.QSlider(QtCore.Qt.Orientation.Horizontal)	#Used to move through all the previous data - Pol 0
		SpectrumSlider = QtGui.QSlider(QtCore.Qt.Orientation.Horizontal)#Used to move the marker through the visible waterfall plot - Pol 0
		#Pol 1
		ZoomSlider_pol1 = QtGui.QSlider(QtCore.Qt.Orientation.Horizontal)	#Used to zoom into the region where the spectrum is being examined - Pol 1
		ScrollSlider_pol1 = QtGui.QSlider(QtCore.Qt.Orientation.Horizontal)	#Used to move through all the previous data - Pol 1
		SpectrumSlider_pol1 = QtGui.QSlider(QtCore.Qt.Orientation.Horizontal)#Used to move the marker through the visible waterfall plot - Pol 1

		#Pol 0
		ZoomSlider.setRange(sampleTimeValue, maximumTime)
		ZoomSlider.setValue(sampleTimeValue)
		ZoomSlider.valueChanged.connect(lambda: self._sliderChanged('pol0'))
		#Pol 1
		ZoomSlider_pol1.setRange(sampleTimeValue, maximumTime)
		ZoomSlider_pol1.setValue(sampleTimeValue)
		ZoomSlider_pol1.valueChanged.connect(lambda: self._sliderChanged('pol1'))

		#Pol 0
		ScrollSlider.setRange(timeRegionValue, maximumTime)
		ScrollSlider.setValue(timeRegionValue)
		ScrollSlider.valueChanged.connect(lambda: self._sliderChanged('pol0'))
		#Pol 1
		ScrollSlider_pol1.setRange(timeRegionValue, maximumTime)
		ScrollSlider_pol1.setValue(timeRegionValue)
		ScrollSlider_pol1.valueChanged.connect(lambda: self._sliderChanged('pol1'))

		#Pol 0
		SpectrumSlider.setRange(timeRegionValue,timeRegionValue+sampleTimeValue)
		SpectrumSlider.setValue(0)
		SpectrumSlider.valueChanged.connect(lambda: self._spectrumChanged('pol0'))
		#Pol 1
		SpectrumSlider_pol1.setRange(timeRegionValue,timeRegionValue+sampleTimeValue)
		SpectrumSlider_pol1.setValue(0)
		SpectrumSlider_pol1.valueChanged.connect(lambda: self._spectrumChanged('pol1'))

		#Pol 0
		checkboxAverage = QtGui.QCheckBox("Display Average")
		checkboxAverage.setChecked(False)
		checkboxAverage.toggled.connect(lambda: self.Averagecheckbox_toggled('pol0'))
		#Pol 1
		checkboxAverage_pol1 = QtGui.QCheckBox("Display Average")
		checkboxAverage_pol1.setChecked(False)
		checkboxAverage_pol1.toggled.connect(lambda: self.Averagecheckbox_toggled('pol1'))

		#Pol 0
		self.graphZoomSlider = ZoomSlider
		self.graphScrollSlider = ScrollSlider
		self.spectrumSlider = SpectrumSlider
		self.checkboxAverage = checkboxAverage
		#Pol 1
		self.graphZoomSlider_pol1 = ZoomSlider_pol1
		self.graphScrollSlider_pol1 = ScrollSlider_pol1
		self.spectrumSlider_pol1 = SpectrumSlider_pol1
		self.checkboxAverage_pol1 = checkboxAverage_pol1

		#Pol 0
		self.spinBoxDayZoom = QtGui.QSpinBox()
		self.spinBoxHrsZoom = QtGui.QSpinBox()
		self.spinBoxMinZoom = QtGui.QSpinBox()
		self.spinBoxDayScale= QtGui.QSpinBox()
		self.spinBoxHrsScale = QtGui.QSpinBox()
		self.spinBoxMinScale = QtGui.QSpinBox()
		self.spinBoxDayZoom.setProperty("value", 0)
		self.spinBoxHrsZoom.setProperty("value", 0)
		self.spinBoxMinZoom.setProperty("value", 0)
		self.spinBoxDayScale.setProperty("value", 0)
		self.spinBoxHrsScale.setProperty("value", 0)
		self.spinBoxMinScale.setProperty("value", 0)
		self.spinBoxDayZoom.setRange(0,365)
		self.spinBoxHrsZoom.setRange(0,23)
		self.spinBoxMinZoom.setRange(0,59)
		self.spinBoxDayScale.setRange(0,365)
		self.spinBoxHrsScale.setRange(0,23)
		self.spinBoxMinScale.setRange(0,59)
		self.spinBoxDayZoom.valueChanged.connect(lambda: self._spinChanged('pol0'))
		self.spinBoxHrsZoom.valueChanged.connect(lambda: self._spinChanged('pol0'))
		self.spinBoxMinZoom.valueChanged.connect(lambda: self._spinChanged('pol0'))
		self.spinBoxDayScale.valueChanged.connect(lambda: self._spinChanged('pol0'))
		self.spinBoxHrsScale.valueChanged.connect(lambda: self._spinChanged('pol0'))
		self.spinBoxMinScale.valueChanged.connect(lambda: self._spinChanged('pol0'))
		self.lowValue = QtGui.QLabel()
		self.highValue = QtGui.QLabel()

		#Pol 1
		self.spinBoxDayZoom_pol1 = QtGui.QSpinBox()
		self.spinBoxHrsZoom_pol1 = QtGui.QSpinBox()
		self.spinBoxMinZoom_pol1 = QtGui.QSpinBox()
		self.spinBoxDayScale_pol1 = QtGui.QSpinBox()
		self.spinBoxHrsScale_pol1 = QtGui.QSpinBox()
		self.spinBoxMinScale_pol1 = QtGui.QSpinBox()
		self.spinBoxDayZoom_pol1.setProperty("value", 0)
		self.spinBoxHrsZoom_pol1.setProperty("value", 0)
		self.spinBoxMinZoom_pol1.setProperty("value", 0)
		self.spinBoxDayScale_pol1.setProperty("value", 0)
		self.spinBoxHrsScale_pol1.setProperty("value", 0)
		self.spinBoxMinScale_pol1.setProperty("value", 0)
		self.spinBoxDayZoom_pol1.setRange(0,365)
		self.spinBoxHrsZoom_pol1.setRange(0,23)
		self.spinBoxMinZoom_pol1.setRange(0,59)
		self.spinBoxDayScale_pol1.setRange(0,365)
		self.spinBoxHrsScale_pol1.setRange(0,23)
		self.spinBoxMinScale_pol1.setRange(0,59)
		self.spinBoxDayZoom_pol1.valueChanged.connect(lambda: self._spinChanged('pol1'))
		self.spinBoxHrsZoom_pol1.valueChanged.connect(lambda: self._spinChanged('pol1'))
		self.spinBoxMinZoom_pol1.valueChanged.connect(lambda: self._spinChanged('pol1'))
		self.spinBoxDayScale_pol1.valueChanged.connect(lambda: self._spinChanged('pol1'))
		self.spinBoxHrsScale_pol1.valueChanged.connect(lambda: self._spinChanged('pol1'))
		self.spinBoxMinScale_pol1.valueChanged.connect(lambda: self._spinChanged('pol1'))
		self.lowValue_pol1 = QtGui.QLabel()
		self.highValue_pol1 = QtGui.QLabel()

		#Pol 0
		graphs = QtGui.QGroupBox('Pol 0 - Graphs')
		graphs.setLayout(QtGui.QGridLayout())
		graphs.layout().addWidget(QtGui.QLabel('Sample Time:'), 0, 0)
		graphs.layout().addWidget(self.graphZoomSlider, 1, 0, 1, 5)
		graphs.layout().addWidget(self.lowValue, 2, 0)
		graphs.layout().addWidget(self.spinBoxDayZoom, 2, 2, 3)
		graphs.layout().addWidget(self.spinBoxHrsZoom, 2, 3, 4)
		graphs.layout().addWidget(self.spinBoxMinZoom, 2, 4, 5)
		graphs.layout().addWidget(QtGui.QLabel('Time Region:'), 3, 0)
		graphs.layout().addWidget(QtGui.QLabel('Days:'), 3, 2)
		graphs.layout().addWidget(QtGui.QLabel('Hours:'), 3, 3, 4)
		graphs.layout().addWidget(QtGui.QLabel('Minutes:'), 3, 4)
		graphs.layout().addWidget(self.graphScrollSlider, 4, 0, 1, 5)
		graphs.layout().addWidget(self.highValue, 5, 0)
		graphs.layout().addWidget(self.spinBoxDayScale, 5, 2, 3)
		graphs.layout().addWidget(self.spinBoxHrsScale, 5, 3, 4)
		graphs.layout().addWidget(self.spinBoxMinScale, 5, 4, 5)
		graphs.layout().addWidget(QtGui.QLabel('Select Individual Spectrum:'), 6, 0)
		graphs.layout().addWidget(QtGui.QLabel('Days:'), 6, 2)
		graphs.layout().addWidget(QtGui.QLabel('Hours:'), 6, 3, 4)
		graphs.layout().addWidget(QtGui.QLabel('Minutes:'), 6, 4)
		graphs.layout().addWidget(self.spectrumSlider, 7, 0, 1, 5)
		graphs.layout().addWidget(QtGui.QLabel('Frequency Spectrum:'), 9, 0)
		graphs.layout().addWidget(self.checkboxAverage, 10, 0, 1, 2)

		#Pol 1
		graphs_pol1 = QtGui.QGroupBox('Pol 1 - Graphs')
		graphs_pol1.setLayout(QtGui.QGridLayout())
		graphs_pol1.layout().addWidget(QtGui.QLabel('Sample Time:'), 0, 0)
		graphs_pol1.layout().addWidget(self.graphZoomSlider_pol1, 1, 0, 1, 5)
		graphs_pol1.layout().addWidget(self.lowValue_pol1, 2, 0)
		graphs_pol1.layout().addWidget(self.spinBoxDayZoom_pol1, 2, 2, 3)
		graphs_pol1.layout().addWidget(self.spinBoxHrsZoom_pol1, 2, 3, 4)
		graphs_pol1.layout().addWidget(self.spinBoxMinZoom_pol1, 2, 4, 5)
		graphs_pol1.layout().addWidget(QtGui.QLabel('Time Region:'), 3, 0)
		graphs_pol1.layout().addWidget(QtGui.QLabel('Days:'), 3, 2)
		graphs_pol1.layout().addWidget(QtGui.QLabel('Hours:'), 3, 3, 4)
		graphs_pol1.layout().addWidget(QtGui.QLabel('Minutes:'), 3, 4)
		graphs_pol1.layout().addWidget(self.graphScrollSlider_pol1, 4, 0, 1, 5)
		graphs_pol1.layout().addWidget(self.highValue_pol1, 5, 0)
		graphs_pol1.layout().addWidget(self.spinBoxDayScale_pol1, 5, 2, 3)
		graphs_pol1.layout().addWidget(self.spinBoxHrsScale_pol1, 5, 3, 4)
		graphs_pol1.layout().addWidget(self.spinBoxMinScale_pol1, 5, 4, 5)
		graphs_pol1.layout().addWidget(QtGui.QLabel('Select Individual Spectrum:'), 6, 0)
		graphs_pol1.layout().addWidget(QtGui.QLabel('Days:'), 6, 2)
		graphs_pol1.layout().addWidget(QtGui.QLabel('Hours:'), 6, 3, 4)
		graphs_pol1.layout().addWidget(QtGui.QLabel('Minutes:'), 6, 4)
		graphs_pol1.layout().addWidget(self.spectrumSlider_pol1, 7, 0, 1, 5)
		graphs_pol1.layout().addWidget(QtGui.QLabel('Frequency Spectrum:'), 9, 0)
		graphs_pol1.layout().addWidget(self.checkboxAverage_pol1, 10, 0, 1, 2)

		self.secondsToTimePol0()	#Set time text for pol0
		self.secondsToTimePol1()	#Set time text for pol1

		tabsGraphsPols	= QtGui.QTabWidget()
		tabsGraphsPols.addTab(graphs,"Pol 0")
		tabsGraphsPols.addTab(graphs_pol1,"Pol 1")


		return (tabsGraphsPols)

	def secondsToTimePol0(self, *fargs):
		# Update UI to represent new slider values
		if (int(time.strftime("%d",time.gmtime(sampleTimeValue)))-1) == 0:
			self.lowValue.setText(time.strftime("%H:%M:%S", time.gmtime(sampleTimeValue)))
		else:
			dayNo = int(time.strftime("%d",time.gmtime(sampleTimeValue)))-1
			self.lowValue.setText(str(dayNo)+' day - '+time.strftime("%H:%M:%S", time.gmtime(sampleTimeValue)))
		if (int(time.strftime("%d",time.gmtime(timeRegionValue)))-1) == 0:
			self.highValue.setText(time.strftime("%H:%M:%S", time.gmtime(timeRegionValue))+' ago')
		else:
			dayNo = int(time.strftime("%d",time.gmtime(timeRegionValue)))-1
			self.highValue.setText(str(dayNo)+' day and '+time.strftime("%H:%M:%S", time.gmtime(timeRegionValue))+' ago')

	def secondsToTimePol1(self, *fargs):
		# Update UI to represent new slider values
		if (int(time.strftime("%d",time.gmtime(sampleTimeValue_pol1)))-1) == 0:
			self.lowValue_pol1.setText(time.strftime("%H:%M:%S", time.gmtime(sampleTimeValue_pol1)))
		else:
			dayNo = int(time.strftime("%d",time.gmtime(sampleTimeValue_pol1)))-1
			self.lowValue_pol1.setText(str(dayNo)+' day - '+time.strftime("%H:%M:%S", time.gmtime(sampleTimeValue_pol1)))
		if (int(time.strftime("%d",time.gmtime(timeRegionValue_pol1)))-1) == 0:
			self.highValue_pol1.setText(time.strftime("%H:%M:%S", time.gmtime(timeRegionValue_pol1))+' ago')
		else:
			dayNo = int(time.strftime("%d",time.gmtime(timeRegionValue_pol1)))-1
			self.highValue_pol1.setText(str(dayNo)+' day and '+time.strftime("%H:%M:%S", time.gmtime(timeRegionValue_pol1))+' ago')


	def _sliderChanged(self, pol):
		global sampleTimeValue, timeRegionValue, slidersHaveBeenChanged, sampleTimeValue_pol1, timeRegionValue_pol1, slidersHaveBeenChanged_pol1
		if pol=='pol0':
			if slidersHaveBeenChanged==False:	#Check if variables haven't already been processed by the spinboxes
				#Keep copy of old values incase new values exceed buffer time
				tempZoom = sampleTimeValue
				tempScroll = timeRegionValue
				#Update variables to new values
				sampleTimeValue=self.graphZoomSlider.value()
				timeRegionValue=self.graphScrollSlider.value()
				#Check if new values exceed maximum buffer time
				if (sampleTimeValue > maximumTime):
					sampleTimeValue = tempZoom
				if (timeRegionValue > maximumTime):
					timeRegionValue = tempScroll

				self.spectrumSlider.setRange(timeRegionValue,timeRegionValue+sampleTimeValue) #Re-adjust range of spectrum slider to cover the visible waterfall spectrum

				lastTimeValue = self.spectrogram.spectPlotPol0.get_extent()
				[top, bottom] = self.spectrogram.spectAxPol0.get_ylim()	#Get bottom stretch of the spectrogram data

				if (lastTimeValue[2]<bottom):	#Check if end of data is visible in spectrogram
					self.spectrumSlider.setRange(timeRegionValue,np.rint(lastTimeValue[2])) 	#Prevent the horizontal slider from exceeding the end of data

				self.secondsToTimePol0()

				slidersHaveBeenChanged=True	#Update state

				# Adjust chart UI with new slider values.
				self.spinBoxDayZoom.setValue(time.gmtime(sampleTimeValue).tm_yday-1)
				self.spinBoxHrsZoom.setValue(time.gmtime(sampleTimeValue).tm_hour)
				self.spinBoxMinZoom.setValue(time.gmtime(sampleTimeValue).tm_min)
				self.spinBoxDayScale.setValue(time.gmtime(timeRegionValue).tm_yday-1)
				self.spinBoxHrsScale.setValue(time.gmtime(timeRegionValue).tm_hour)
				self.spinBoxMinScale.setValue(time.gmtime(timeRegionValue).tm_min)

				self.spectrogram.updateCaptureRange('pol0')

		if pol=='pol1':
			if slidersHaveBeenChanged_pol1==False:	#Check if variables haven't already been processed by the spinboxes
				#Keep copy of old values incase new values exceed buffer time
				tempZoom = sampleTimeValue_pol1
				tempScroll = timeRegionValue_pol1
				#Update variables to new values
				sampleTimeValue_pol1=self.graphZoomSlider_pol1.value()
				timeRegionValue_pol1=self.graphScrollSlider_pol1.value()
				#Check if new values exceed maximum buffer time
				if (sampleTimeValue_pol1 > maximumTime):
					sampleTimeValue_pol1 = tempZoom
				if (timeRegionValue_pol1 > maximumTime):
					timeRegionValue_pol1 = tempScroll

				self.spectrumSlider_pol1.setRange(timeRegionValue_pol1,timeRegionValue_pol1+sampleTimeValue_pol1) #Re-adjust range of spectrum slider to cover the visible waterfall spectrum

				lastTimeValue = self.spectrogram.spectPlotPol1.get_extent()
				[top, bottom] = self.spectrogram.spectAxPol1.get_ylim()	#Get bottom stretch of the spectrogram data

				if (lastTimeValue[2]<bottom):	#Check if end of data is visible in spectrogram
					self.spectrumSlider_pol1.setRange(timeRegionValue_pol1,np.rint(lastTimeValue[2]))#Prevent the horizontal slider from exceeding the end of data

				self.secondsToTimePol1()

				slidersHaveBeenChanged_pol1=True	#Update state

				# Adjust chart UI with new slider values.
				self.spinBoxDayZoom_pol1.setValue(time.gmtime(sampleTimeValue_pol1).tm_yday-1)
				self.spinBoxHrsZoom_pol1.setValue(time.gmtime(sampleTimeValue_pol1).tm_hour)
				self.spinBoxMinZoom_pol1.setValue(time.gmtime(sampleTimeValue_pol1).tm_min)
				self.spinBoxDayScale_pol1.setValue(time.gmtime(timeRegionValue_pol1).tm_yday-1)
				self.spinBoxHrsScale_pol1.setValue(time.gmtime(timeRegionValue_pol1).tm_hour)
				self.spinBoxMinScale_pol1.setValue(time.gmtime(timeRegionValue_pol1).tm_min)

				self.spectrogram.updateCaptureRange('pol1')


	def _spinChanged(self, pol):
		global sampleTimeValue, timeRegionValue, slidersHaveBeenChanged, sampleTimeValue_pol1, timeRegionValue_pol1, slidersHaveBeenChanged_pol1

		if pol=='pol0':
			if slidersHaveBeenChanged==False:	#Check if variables haven't already been processed by the spinboxes
				#Keep copy of old values incase new values exceed buffer time
				tempZoom = sampleTimeValue
				tempScroll = timeRegionValue
				#Update variables to new values
				sampleTimeValue=self.spinBoxDayZoom.value()*86400+self.spinBoxHrsZoom.value()*3600+self.spinBoxMinZoom.value()*60
				timeRegionValue=self.spinBoxDayScale.value()*86400+self.spinBoxHrsScale.value()*3600+self.spinBoxMinScale.value()*60
				#Check if new values exceed maximum buffer time
				if (sampleTimeValue > maximumTime):
					sampleTimeValue = tempZoom
					self.spinBoxDayZoom.setValue(time.gmtime(sampleTimeValue).tm_yday-1)
					self.spinBoxHrsZoom.setValue(time.gmtime(sampleTimeValue).tm_hour)
					self.spinBoxMinZoom.setValue(time.gmtime(sampleTimeValue).tm_min)
				if (timeRegionValue > maximumTime):
					timeRegionValue = tempScroll
					self.spinBoxDayScale.setValue(time.gmtime(timeRegionValue).tm_yday-1)
					self.spinBoxHrsScale.setValue(time.gmtime(timeRegionValue).tm_hour)
					self.spinBoxMinScale.setValue(time.gmtime(timeRegionValue).tm_min)

				if sampleTimeValue<5:	#Set minumum range to 5 seconds not below 5
					sampleTimeValue = 5

				self.spectrumSlider.setRange(timeRegionValue,timeRegionValue+sampleTimeValue) #Re-adjust range of spectrum slider to cover the visible waterfall spectrum

				lastTimeValue = self.spectrogram.spectPlotPol0.get_extent()
				[top, bottom] = self.spectrogram.spectAxPol0.get_ylim()#Get bottom stretch of the spectrogram data

				if (lastTimeValue[2]<bottom):#Check if end of data is visible in spectrogram
					self.spectrumSlider.setRange(timeRegionValue,np.rint(lastTimeValue[2])) #Prevent the horizontal slider from exceeding the end of data

				self.secondsToTimePol0()

				slidersHaveBeenChanged=True	#Update state

				# Adjust chart UI with new slider values.
				self.graphZoomSlider.setValue(sampleTimeValue)
				self.graphScrollSlider.setValue(timeRegionValue)

				self.spectrogram.updateCaptureRange('pol0')

		if pol=='pol1':
			if slidersHaveBeenChanged_pol1==False:	#Check if variables haven't already been processed by the spinboxes
				#Keep copy of old values incase new values exceed buffer time
				tempZoom = sampleTimeValue_pol1
				tempScroll = timeRegionValue_pol1
				#Update variables to new values
				sampleTimeValue_pol1=self.spinBoxDayZoom_pol1.value()*86400+self.spinBoxHrsZoom_pol1.value()*3600+self.spinBoxMinZoom_pol1.value()*60
				timeRegionValue_pol1=self.spinBoxDayScale_pol1.value()*86400+self.spinBoxHrsScale_pol1.value()*3600+self.spinBoxMinScale_pol1.value()*60
				#Check if new values exceed maximum buffer time
				if (sampleTimeValue_pol1 > maximumTime):
					sampleTimeValue_pol1 = tempZoom
					self.spinBoxDayZoom_pol1.setValue(time.gmtime(sampleTimeValue_pol1).tm_yday-1)
					self.spinBoxHrsZoom_pol1.setValue(time.gmtime(sampleTimeValue_pol1).tm_hour)
					self.spinBoxMinZoom_pol1.setValue(time.gmtime(sampleTimeValue_pol1).tm_min)
				if (timeRegionValue_pol1 > maximumTime):
					timeRegionValue_pol1 = tempScroll
					self.spinBoxDayScale_pol1.setValue(time.gmtime(timeRegionValue_pol1).tm_yday-1)
					self.spinBoxHrsScale_pol1.setValue(time.gmtime(timeRegionValue_pol1).tm_hour)
					self.spinBoxMinScale_pol1.setValue(time.gmtime(timeRegionValue_pol1).tm_min)

				if sampleTimeValue_pol1<5:	#Set minumum range to 5 seconds not below 5
					sampleTimeValue_pol1 = 5

				self.spectrumSlider_pol1.setRange(timeRegionValue_pol1,timeRegionValue_pol1+sampleTimeValue_pol1) #Re-adjust range of spectrum slider to cover the visible waterfall spectrum

				lastTimeValue = self.spectrogram.spectPlotPol1.get_extent()
				[top, bottom] = self.spectrogram.spectAxPol1.get_ylim()#Get bottom stretch of the spectrogram data

				if (lastTimeValue[2]<bottom):#Check if end of data is visible in spectrogram
					self.spectrumSlider_pol1.setRange(timeRegionValue_pol1,np.rint(lastTimeValue[2])) #Prevent the horizontal slider from exceeding the end of data

				self.secondsToTimePol1()

				slidersHaveBeenChanged_pol1=True	#Update state

				# Adjust chart UI with new slider values.
				self.graphZoomSlider_pol1.setValue(sampleTimeValue_pol1)
				self.graphScrollSlider_pol1.setValue(timeRegionValue_pol1)

				self.spectrogram.updateCaptureRange('pol1')

	def _spectrumChanged(self, pol):
		global spectrumNumberScale, slidersHaveBeenChanged, horizontalslidersHaveBeenChanged, spectrumNumberScale_pol1,\
		slidersHaveBeenChanged_pol1, horizontalslidersHaveBeenChanged_pol1
		if pol=='pol0':
			self.checkSpectrumSlider('pol0')
			spectrumNumberScale = self.spectrumSlider.value()	#Store new spectrum number from the UI
			horizontalslidersHaveBeenChanged=True
		if pol=='pol1':
			self.checkSpectrumSlider('pol1')
			spectrumNumberScale_pol1 = self.spectrumSlider_pol1.value()	#Store new spectrum number from the UI
			horizontalslidersHaveBeenChanged_pol1=True

	def Lockedcheckbox_toggled(self, value):
		global isLocked
		if isLocked:
			isLocked=False
		else:
			isLocked=True

	def Averagecheckbox_toggled(self, pol):
		global displayAverage,horizontalslidersHaveBeenChanged, displayAverage_pol1
		if pol=='pol0':
			if displayAverage:
				self.spectrogram.histAxPol0.set_title('Frequency Spectrum')
				displayAverage=False
				horizontalslidersHaveBeenChanged=True	#Disable the spectrum slider
			else:
				displayAverage=True
				self.spectrogram.hline.set_ydata(0)
				extentValue = self.spectrogram.spectPlotPol0.get_extent()
				[top, bottom] = self.spectrogram.spectAxPol0.get_ylim()
				if(extentValue[2] < top):	#If the end of the waterfall is visible, set the top to the end of the spectrum
					top = np.rint(extentValue[2])
				bottom = np.rint(bottom/snapboard_capture_time)	#Scale to array indexes (snapboard_capture_time refers to the average storing time from SnapBoard)
				top = np.rint(top/snapboard_capture_time)	#Scale to array indexes (snapboard_capture_time refers to the average storing time from SnapBoard)
				self.spectrogram.average_data = np.mean(self.spectrogram.pol0[bottom:(top+1),:], axis = 0)	#Get average from bottom to top of spectrogram
				histData = np.log(self.spectrogram.average_data)
				histData_dB = 10*np.log10(2**histData)
				self.spectrogram.histPlotPol0.set_ydata(histData_dB)
				self.spectrogram.histAxPol0.set_title('Frequency Spectrum (Average)')
		if pol=='pol1':
			if displayAverage_pol1:
				self.spectrogram.histAxPol1.set_title('Frequency Spectrum')
				displayAverage_pol1=False
				horizontalslidersHaveBeenChanged_pol1=True	#Disable the spectrum slider
			else:
				displayAverage_pol1=True
				self.spectrogram.hline_pol1.set_ydata(0)
				extentValue = self.spectrogram.spectPlotPol1.get_extent()
				[top, bottom] = self.spectrogram.spectAxPol1.get_ylim()
				if(extentValue[2] < top):	#If the end of the waterfall is visible, set the top to the end of the spectrum
					top = np.rint(extentValue[2])
				bottom = np.rint(bottom/snapboard_capture_time)	#Scale to array indexes (snapboard_capture_time refers to the average storing time from SnapBoard)
				top = np.rint(top/snapboard_capture_time)	#Scale to array indexes (snapboard_capture_time refers to the average storing time from SnapBoard)
				self.spectrogram.average_data_pol1 = np.mean(self.spectrogram.pol1[bottom:(top+1),:], axis = 0)	#Get average from bottom to top of spectrogram
				histData = np.log(self.spectrogram.average_data_pol1)
				histData_dB = 10*np.log10(2**histData)
				self.spectrogram.histPlotPol1.set_ydata(histData_dB)
				self.spectrogram.histAxPol1.set_title('Frequency Spectrum (Average)')

	def _calibrateBtn(self):
		global displayAverage, timeRegionValue, sampleTimeValue

		self.spectrogram.horizontalMarker = 0	#This is the variable that stores the height of the spectrum marker on the interface (black dashed line)
		self.spectrogram.horizontalMarker_pol1 = 0	#This is the variable that stores the height of the spectrum marker on the interface (black dashed line)

		self.spectrogram.initializePol0()
		self.spectrogram.initializePol1()

		#Pol 0
		if displayAverage:
			self.spectrogram.histAxPol0.set_title('Frequency Spectrum (Average)')
			self.spectrogram.average_data = np.mean(self.spectrogram.pol0, axis = 0)
			histData = np.log(self.spectrogram.average_data)
			histData_dB = 10*np.log10(2**histData)
		else:
			self.spectrogram.hline = self.spectrogram.spectAxPol0.axhline(self.spectrogram.horizontalMarker, color='k', linestyle='--', linewidth=2)	#Create new horizontal line
			self.spectrogram.hline.set_ydata(0)
			spectrumMarkerRounded = np.rint(self.spectrogram.spectrumMarker)
			self.spectrogram.data = self.spectrogram.pol0[spectrumMarkerRounded]
			self.spectrumSlider.setValue(0)
		self.secondsToTimePol0()

		#Pol 1
		if displayAverage_pol1:
			self.spectrogram.histAxPol1.set_title('Frequency Spectrum (Average)')
			self.spectrogram.average_data_pol1 = np.mean(self.spectrogram.pol1, axis = 0)
			histData = np.log(self.spectrogram.average_data_pol1)
			histData_dB = 10*np.log10(2**histData)
		else:
			self.spectrogram.hline_pol1 = self.spectrogram.spectAxPol1.axhline(self.spectrogram.horizontalMarker_pol1, color='k', linestyle='--', linewidth=2)	#Create new horizontal line
			self.spectrogram.hline_pol1.set_ydata(0)
			spectrumMarkerRounded = np.rint(self.spectrogram.spectrumMarker_pol1)
			self.spectrogram.data_pol1 = self.spectrogram.pol1[spectrumMarkerRounded]
			self.spectrumSlider_pol1.setValue(0)
		self.secondsToTimePol1()


	def _clearBtn(self):
		retval = self.showClearDataDialog()
		if(retval == QtGui.QMessageBox.Ok):
			self.spectrogram.pol0 = np.delete(self.spectrogram.pol0, slice(0,self.spectrogram.num_rows), axis=0)
			self.spectrogram.spectPlotPol0.set_extent([0,250,0,0])
			self.spectrogram.hline.set_ydata(0)
			self.spectrogram.pol1 = np.delete(self.spectrogram.pol1, slice(0,self.spectrogram.num_rows_pol1), axis=0)
			self.spectrogram.spectPlotPol1.set_extent([0,250,0,0])
			self.spectrogram.hline_pol1.set_ydata(0)

	def setMaximumTime(self):
		global maximumTime
		newTime = (86400*self.spinBoxDay.value()) + (3600*self.spinBoxHour.value()) + (60*self.spinBoxMinute.value())

		lastTimeValue = self.spectrogram.spectPlotPol0.get_extent()	#Get the bottom of the spectrum on the waterfall plot. 'pol0.scio' and 'pol1.scio' should have the same number of spectrum

		if newTime==0:	#If zero time is entered, reset to one day
			maximumTime=86400
			self.spinBoxDay.setValue(1)
			self._zeroMaxTimeError()
		else:
			if (newTime < lastTimeValue[2]):	#If buffer time is shorter than the elapsed spectra time. Show error
				retval = self.showMaxTimeDialog()	#If user accepts, cut off exceeding time
				if(retval == QtGui.QMessageBox.Ok):
					maximumTime = newTime
					self.graphScrollSlider.setRange(0, maximumTime)
					self.graphZoomSlider.setRange(5, maximumTime)
					self.spectrumSlider.setRange(timeRegionValue,timeRegionValue+sampleTimeValue)
				else:	#Else cancel
					self.spinBoxDay.setValue(time.gmtime(maximumTime).tm_yday-1)
					self.spinBoxHour.setValue(time.gmtime(maximumTime).tm_hour)
					self.spinBoxMinute.setValue(time.gmtime(maximumTime).tm_min)
			else:
				maximumTime = newTime
				self.graphScrollSlider.setRange(0, maximumTime)	#Update sliders to represent the new buffer time
				self.graphZoomSlider.setRange(5, maximumTime)
				self.spectrumSlider.setRange(timeRegionValue,timeRegionValue+sampleTimeValue)


	def checkSpectrumSlider(self,pol):
		'''Check if new slider position exceeds the data on the spectrogram'''
		if(pol=='pol0'):
			lastTimeValue = self.spectrogram.spectPlotPol0.get_extent()
			[top, bottom] = self.spectrogram.spectAxPol0.get_ylim()
			if(lastTimeValue[2] < top):
				self.spectrumSlider.setRange(timeRegionValue,np.rint(lastTimeValue[2])) #Ensure that the range of the spectrum slider does not exceed data size
			else:
				self.spectrumSlider.setRange(timeRegionValue,timeRegionValue+sampleTimeValue) #Else let spectrum slider cover the colormap
		if(pol=='pol1'):
			lastTimeValue = self.spectrogram.spectPlotPol1.get_extent()
			[top, bottom] = self.spectrogram.spectAxPol1.get_ylim()
			if(lastTimeValue[2] < top):
				self.spectrumSlider_pol1.setRange(timeRegionValue_pol1,np.rint(lastTimeValue[2]))#Ensure that the range of the spectrum slider does not exceed data size
			else:
				self.spectrumSlider_pol1.setRange(timeRegionValue_pol1,timeRegionValue_pol1+sampleTimeValue_pol1)#Else let spectrum slider cover the colormap

	def showMaxTimeDialog(self):
		msg = QtGui.QMessageBox()
		msg.setIcon(QtGui.QMessageBox.Warning)
		msg.setText("Buffer time shorter than waterfall spectrum time")
		msg.setInformativeText("The buffer time you chose precedes the time used to capture spectrum data. Should you persist in with this buffer time, this will result in loss of the older data. Do you accept?")
		msg.setWindowTitle("Buffer Time Warning")
		msg.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
		return msg.exec_()

	def showClearDataDialog(self):
		msg = QtGui.QMessageBox()
		msg.setIcon(QtGui.QMessageBox.Warning)
		msg.setText("Clear capture data to release memory")
		msg.setInformativeText("Should you persist, this will result in loss of all the captured data. Do you accept?")
		msg.setWindowTitle("Clear Captured Data?")
		msg.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
		return msg.exec_()

	def _zeroMaxTimeError(self):
		msg = QtGui.QMessageBox()
		msg.setIcon(QtGui.QMessageBox.Information)
		msg.setWindowTitle("Invalid Buffer Time")
		msg.setText('Cannot have a zero buffer time')
		msg.exec_()
