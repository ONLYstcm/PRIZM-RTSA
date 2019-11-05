import time
import os
import scio
import numpy as np

from matplotlib.cm import get_cmap
from matplotlib.ticker import FuncFormatter
from PyQt5 import QtCore, QtGui, QtWidgets

global maximumTime, spectrumCounter, isLocked, lockedPlotEvent, snapboard_capture_time

# These global variables are used to keep track of the interface states
isLocked = False
lockedPlotEvent = 0
spectrumCounter = 0
# The 'snapboard_capture_time' value represents the average number of seconds taken to acquire the data SnapBoard.
# You may change this to suit the time taken on your system
snapboard_capture_time=3.3
# This is the default maximum buffer time (it corresponds to a day)
maximumTime = 86400

# Check if file exists and is not empty
def is_non_zero_file(fpath): 
    return os.path.isfile(fpath) and os.path.getsize(fpath) > 0

class pol():
	def __init__(self, pole, cwd, filename):
		# Default parameters
		self.sampleTimeValue=5
		self.timeRegionValue=0
		self.spectrumNumberScale=0
		self.slidersHaveBeenChanged=False
		self.horizontalslidersHaveBeenChanged=False
		self.displayAverage=False
		self.has_been_initialised=False

		self.horizontalMarker = 0	# This is the variable that stores the height of the spectrum marker on the interface (black dashed line)
		self.spectrumMarker = 0		# This is the variable that stores the spectrum number in the array
		self.maxExtentStretch = 60	# This is the maximum height to which the waterfall plot is stretched to

		self.init_num_rows = 0
		self.init_num_cols = 0
		self.pole = pole
		self.cwd = cwd
		self.filename = filename

	def createFigure(self, figure, gs):
		# Set up spectrogram waterfall plot
		self.spectAx = figure.add_subplot(gs[2])
		self.spectAx.set_title('Spectrogram - Pol %s' % self.pole)
		self.spectAx.set_ylabel('Sample Age (seconds)')
		self.spectAx.set_xlabel('Frequency Bin (MHz)')
		self.spectAx.set_xlim(left=0, right=250)
		# Create empty waterfall plot variable
		self.spectPlot = self.spectAx.imshow(([],[]), aspect='auto', cmap=get_cmap('jet'))

		# Set up frequency histogram bar plot
		self.histAx = figure.add_subplot(gs[0])
		self.histAx.set_title('Frequency Spectrum - Pol %s' % self.pole)
		self.histAx.set_ylabel('Intensity (dB)')
		self.histAx.set_xlim(left=0, right=250)
		# Create empty spectrogram plot variable
		self.histPlot, = self.histAx.plot([],[])

	def initialize(self):
		# Reset graphs
		self.spectAx.cla()
		self.histAx.cla()

		# Setup spectrum graph
		self.histAx.set_title('Frequency Spectrum - Pol %s' % self.pole)
		self.histAx.set_ylabel('Intensity (dB)')
		self.histAx.set_xlim(left=0, right=250)
		self.histAx.callbacks.connect('xlim_changed', self.spectXlimUpdate())	#Setup lock feature in pan and zoom

		# Setup waterfall graph
		self.spectAx.set_title('Spectrogram - Pol %s' % self.pole)
		self.spectAx.set_ylabel('Sample Age (seconds)')
		self.spectAx.set_xlabel('Frequency Bin (MHz)')
		self.spectAx.set_xlim(left=0, right=250)
		self.spectAx.callbacks.connect('xlim_changed', self.histXlimUpdate())	#Setup lock feature in pan and zoom

		# Read the correct file by giving the right path
		self.data = scio.read('%s' % self.cwd + '/%s' % self.filename)
		self.num_rows, self.num_cols = np.shape(self.data)

		# Define the x-axis to span 0--250 MHz
		self.frequency = np.linspace(0,250,4096)

		# Setup waterfall plot
		self.init_num_rows, self.init_num_cols = np.shape(self.data)
		self.waterfall = np.log10(np.abs(self.data))
		self.median = np.median(self.waterfall)
		self.std = np.std(self.waterfall)
		self.vmin , self.vmax = (self.median-self.std) , (self.median+self.std)
		self.nu=((np.arange(self.waterfall.shape[1])+0.5)/(1.0*self.waterfall.shape[1]))*250; # frequency range in MHz
		self.spectPlot = self.spectAx.imshow(self.waterfall, aspect='auto', cmap='jet',extent=[0,250,24,0],vmin=self.vmin,vmax=self.vmax)

		# This equation pulls all the initial data from the 'scio' and gets the time exceeded by multiplying the number of spectra with snapboard_capture_time
		self.maxExtentStretch = self.init_num_rows*snapboard_capture_time
		self.spectPlot.set_extent([0,250,self.maxExtentStretch,0])
		self.spectAx.set_ylim(top=self.timeRegionValue, bottom=self.timeRegionValue+self.sampleTimeValue)
		self.ymin, self.ymax = self.spectAx.get_ylim()

		# Save plotting data
		data = self.data[self.init_num_rows-self.horizontalMarker-1,:]

		# Take a mean along the rows
		self.average_data = np.mean(self.data, axis = 0)
		histData = np.log(data)
		histData_dB = 10*np.log10(2**histData)
		self.histPlot, = self.histAx.plot(self.frequency,histData_dB)

		# Get limits of the waterfall plot; these variable are used when zooming into the subplot
		self.ymin, self.ymax = self.spectAx.get_ylim()

	# Update limits to spectrogram
	def histXlimUpdate(self):
		if isLocked:
			if lockedPlotEvent == 0:
				lockedPlotEvent = 1
				self.histAx.set_xlim(self.spectAx.get_xlim())
			else:
				lockedPlotEvent = 0
			return lockedPlotEvent

	# Update limits to frequency spectrum
	def spectXlimUpdate(self):
		if isLocked:
			if lockedPlotEvent == 0:
				lockedPlotEvent = 1
				self.spectAx.set_xlim(self.histAx.get_xlim())
			else:
				lockedPlotEvent = 0
			return lockedPlotEvent

	def update(self):
		if is_non_zero_file('%s' % self.cwd + '/%s' % self.filename):
			# Initialize spectrum plots if not done before
			if not self.has_been_initialised:
				self.initialize()
				#This is the marker which spreads across the graphs
				self.hline = self.spectAx.axhline(self.horizontalMarker, color='k', linestyle='--', linewidth=2)
				self.has_been_initialised = True

			# Read the correct file by giving the right path
			arrayTemp = scio.read('%s' % self.cwd + '/%s' % self.filename)
			self.num_rows, self.num_cols = np.shape(arrayTemp)

			if self.init_num_rows != self.num_rows:	
				# Check if the number of rows has changed implying a new spectrum is present
				try:
					self.data = np.vstack([arrayTemp[spectrumCounter],self.data])
				except IndexError:	
				# Else the new number of spectrum is smaller than the previous because a new file is created ('scio' file has changed folders in the snapboard)
					spectrumCounter=0
					self.data = np.vstack([arrayTemp[spectrumCounter],self.data])

				# Update number of rows
				self.init_num_rows = self.num_rows

				self.num_rows, self.num_cols = np.shape(self.pol0)
				self.waterfall = np.log10(np.abs(self.pol0))
				self.median = np.median(self.waterfall)
				self.std = np.std(self.waterfall)
				self.vmin , self.vmax = (self.median-self.std) , (self.median+self.std)
				# frequency range in MHz
				self.nu=((np.arange(self.waterfall.shape[1])+0.5)/(1.0*self.waterfall.shape[1]))*250
				self.spectPlot.set_data(self.waterfall)
				self.extendYaxis(snapboard_capture_time)

				# Update spectrum according to the states of the interface
				if self.displayAverage:
					extentValue = self.spectPlot.get_extent()
					[top, bottom] = self.spectAx.get_ylim()
					# If the end of the waterfall is visible, set the top to the end of the spectrum
					if(extentValue[2] < top):
						top = int(np.rint(extentValue[2]))
					# Scale back for array indexing
					bottom = int(np.rint(bottom/snapboard_capture_time))
					# Scale back for array indexing
					top = int(np.rint(top/snapboard_capture_time))
					# Get average spectrum of data displayed on the waterfall plot
					self.average_data = np.mean(self.data[bottom:(top+1),:], axis = 0)
					histData = np.log(self.average_data)
					histData_dB = 10*np.log10(2**histData)
					self.histPlot.set_ydata(histData_dB)
				else:
					# Get value from the UI slider
					self.horizontalMarker = self.spectrumNumberScale
					# Scale down by 'snapboard_capture_time' for array indexing
					self.spectrumMarker = self.horizontalMarker/snapboard_capture_time
					# Set black marker at location
					self.hline.set_ydata(self.horizontalMarker)
					spectrumMarkerRounded = int(np.rint(self.spectrumMarker))
					print(spectrumMarkerRounded)
					try:
						data = self.data[spectrumMarkerRounded]
					except IndexError:
						data = self.data[0]
					histData = np.log(data)
					histData_dB = 10*np.log10(2**histData)
					self.histPlot.set_ydata(histData_dB)


	def updateAxis(self):
		if self.slidersHaveBeenChanged:
			# Update frequency spectrum to display 'average' spectra or selected spectra
			self.spectPlot.set_data(self.waterfall)
			self.slidersHaveBeenChanged=False
		if self.horizontalslidersHaveBeenChanged and not self.displayAverage:
			# Get value from UI slider
			self.horizontalMarker = self.spectrumNumberScale
			# Scale the UI slider to the index of the array in pol0
			self.spectrumMarker = (self.horizontalMarker/(self.num_rows*snapboard_capture_time))*(self.num_rows-1)
			spectrumMarkerRounded = int(np.rint(self.spectrumMarker))
			self.hline.set_ydata(self.horizontalMarker)
			try:
				data = self.data[spectrumMarkerRounded]
			except IndexError:
				data = self.data[0]
			histData = np.log(data)
			histData_dB = 10*np.log10(2**histData)
			self.histPlot.set_ydata(histData_dB)
			self.horizontalslidersHaveBeenChanged = False


	def updateCaptureRange(self):
		"""Adjust low and high intensity limits for histogram and spectrum axes."""
		#Convert values to time format
		daysZoom = self.sampleTimeValue//86399
		hoursZoom = self.sampleTimeValue//3599
		minutesZoom = self.sampleTimeValue//59
		daysScroll = self.timeRegionValue//86399
		hoursScroll = self.timeRegionValue//3599
		minutesScroll = self.timeRegionValue//59

		# Update waterfall limits according to UI values
		self.spectAx.set_ylim(top=self.timeRegionValue, bottom=self.timeRegionValue+self.sampleTimeValue)
		# Update min and max values
		self.ymin, self.ymax = self.spectAx.get_ylim()

		# Display numbers in time format
		if (daysZoom or daysScroll) == 0:
			if (hoursZoom or hoursScroll) == 0:
				if (minutesZoom or minutesScroll) == 0:
					self.spectAx.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%d' % (x*1)))
				else:
					self.spectAx.set_ylabel('Sample Age (minutes:seconds)')
					self.spectAx.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%s' %(time.strftime("%M:%S", time.gmtime(x)))))
			else:
				self.spectAx.set_ylabel('Sample Age (hours:minutes)')
				self.spectAx.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%s' %(time.strftime("%H:%M", time.gmtime(x)))))
		else:
			self.spectAx.set_ylabel('Sample Age (days-hour)')
			self.spectAx.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%s' %('Day '+str(int(time.strftime("%d", time.gmtime(x)))-1)+(time.strftime("-%H:%M", time.gmtime(x))))))

	def extendYaxis(self, value):
		extended = self.spectPlot.get_extent()
		# Get the bottom value where the data is squeezed
		extended = extended[2]+value
		if extended <= (maximumTime+snapboard_capture_time):
			# If end of the spectrum is visible, stretch the data to the end of the spectrum and not the bottom of the axes
			self.spectPlot.set_extent([0,250,extended,0])
		else:
			# Number of rows outside the buffer time
			excessRows = int((extended - maximumTime)//snapboard_capture_time)
			# Delete the array variables outside the buffer time
			self.data = np.delete(self.data, slice(self.num_rows-excessRows, self.num_rows), axis=0)
			if (excessRows > 1):
				self.spectPlot.set_extent([0,250,extended-snapboard_capture_time*excessRows,0])


	def initWidget(self):
		self.graphZoomSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)	#Used to zoom into the region where the spectrum is being examined - Pol 0
		self.graphScrollSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)	#Used to move through all the previous data - Pol 0
		self.spectrumSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)#Used to move the marker through the visible waterfall plot - Pol 0

		# Configure zoom slider
		self.graphZoomSlider.setRange(self.sampleTimeValue, maximumTime)
		self.graphZoomSlider.setValue(self.sampleTimeValue)
		self.graphZoomSlider.valueChanged.connect(lambda: self.sliderChanged(maximumTime))

		# Configure scroll slider
		self.graphScrollSlider.setRange(self.timeRegionValue, maximumTime)
		self.graphScrollSlider.setValue(self.timeRegionValue)
		self.graphScrollSlider.valueChanged.connect(lambda: self.sliderChanged(maximumTime))

		# Configure spectrum slider
		self.spectrumSlider.setRange(self.timeRegionValue,self.timeRegionValue+self.sampleTimeValue)
		self.spectrumSlider.setValue(0)
		self.spectrumSlider.valueChanged.connect(lambda: self.spectrumChanged())

		# Checkbox
		self.checkboxAverage = QtWidgets.QCheckBox("Display Average")
		self.checkboxAverage.setChecked(False)
		self.checkboxAverage.toggled.connect(lambda: self.Averagecheckbox_toggled())

		# Time selectors
		self.spinBoxDayZoom = QtWidgets.QSpinBox()
		self.spinBoxHrsZoom = QtWidgets.QSpinBox()
		self.spinBoxMinZoom = QtWidgets.QSpinBox()
		self.spinBoxDayScale= QtWidgets.QSpinBox()
		self.spinBoxHrsScale = QtWidgets.QSpinBox()
		self.spinBoxMinScale = QtWidgets.QSpinBox()
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
		self.spinBoxDayZoom.valueChanged.connect(lambda: self.spinChanged())
		self.spinBoxHrsZoom.valueChanged.connect(lambda: self.spinChanged())
		self.spinBoxMinZoom.valueChanged.connect(lambda: self.spinChanged())
		self.spinBoxDayScale.valueChanged.connect(lambda: self.spinChanged())
		self.spinBoxHrsScale.valueChanged.connect(lambda: self.spinChanged())
		self.spinBoxMinScale.valueChanged.connect(lambda: self.spinChanged())
		self.lowValue = QtWidgets.QLabel()
		self.highValue = QtWidgets.QLabel()

		# Setup layout of widgets
		self.graphs = QtWidgets.QGroupBox('Pol %s - Graph' % self.pole)
		self.graphs.setLayout(QtWidgets.QGridLayout())
		self.graphs.layout().addWidget(QtWidgets.QLabel('Sample Time:'), 0, 0)
		self.graphs.layout().addWidget(self.graphZoomSlider, 1, 0, 1, 5)
		self.graphs.layout().addWidget(self.lowValue, 2, 0)
		self.graphs.layout().addWidget(self.spinBoxDayZoom, 2, 2)
		self.graphs.layout().addWidget(self.spinBoxHrsZoom, 2, 3)
		self.graphs.layout().addWidget(self.spinBoxMinZoom, 2, 4)
		self.graphs.layout().addWidget(QtWidgets.QLabel('Time Region:'), 3, 0)
		self.graphs.layout().addWidget(QtWidgets.QLabel('Days:'), 3, 2)
		self.graphs.layout().addWidget(QtWidgets.QLabel('Hours:'), 3, 3)
		self.graphs.layout().addWidget(QtWidgets.QLabel('Minutes:'), 3, 4)
		self.graphs.layout().addWidget(self.graphScrollSlider, 4, 0, 1, 5)
		self.graphs.layout().addWidget(self.highValue, 5, 0)
		self.graphs.layout().addWidget(self.spinBoxDayScale, 5, 2)
		self.graphs.layout().addWidget(self.spinBoxHrsScale, 5, 3)
		self.graphs.layout().addWidget(self.spinBoxMinScale, 5, 4)
		self.graphs.layout().addWidget(QtWidgets.QLabel('Select Individual Spectrum:'), 6, 0)
		self.graphs.layout().addWidget(QtWidgets.QLabel('Days:'), 6, 2)
		self.graphs.layout().addWidget(QtWidgets.QLabel('Hours:'), 6, 3)
		self.graphs.layout().addWidget(QtWidgets.QLabel('Minutes:'), 6, 4)
		self.graphs.layout().addWidget(self.spectrumSlider, 7, 0, 1, 5)
		self.graphs.layout().addWidget(QtWidgets.QLabel('Frequency Spectrum:'), 9, 0)
		self.graphs.layout().addWidget(self.checkboxAverage, 10, 0, 1, 2)

	def sliderChanged(self, maximumTime):
		# Check if variables haven't already been processed by the spinboxes
		if self.slidersHaveBeenChanged==False:
			# Keep copy of old values incase new values exceed buffer time
			tempZoom = self.sampleTimeValue
			tempScroll = self.timeRegionValue
			# Update variables to new values
			self.sampleTimeValue=self.graphZoomSlider.value()
			self.timeRegionValue=self.graphScrollSlider.value()
			# Check if new values exceed maximum buffer time
			if (self.sampleTimeValue > maximumTime):
				self.sampleTimeValue = tempZoom
			if (self.timeRegionValue > maximumTime):
				self.timeRegionValue = tempScroll
			# Re-adjust range of spectrum slider to cover the visible waterfall spectrum
			self.spectrumSlider.setRange(self.timeRegionValue, self.timeRegionValue + self.sampleTimeValue)

			lastTimeValue = self.spectPlot.get_extent()
			# Get bottom stretch of the spectrogram data
			[top, bottom] = self.spectAx.get_ylim()

			# Check if end of data is visible in spectrogram
			if (lastTimeValue[2]<bottom):	
				# Prevent the horizontal slider from exceeding the end of data
				self.spectrumSlider.setRange(self.timeRegionValue, int(np.rint(lastTimeValue[2]))) 	
			
			self.secondsToTime()
			# Update state
			self.slidersHaveBeenChanged=True

			# Adjust chart UI with new slider values.
			self.spinBoxDayZoom.setValue(time.gmtime(self.sampleTimeValue).tm_yday-1)
			self.spinBoxHrsZoom.setValue(time.gmtime(self.sampleTimeValue).tm_hour)
			self.spinBoxMinZoom.setValue(time.gmtime(self.sampleTimeValue).tm_min)
			self.spinBoxDayScale.setValue(time.gmtime(self.timeRegionValue).tm_yday-1)
			self.spinBoxHrsScale.setValue(time.gmtime(self.timeRegionValue).tm_hour)
			self.spinBoxMinScale.setValue(time.gmtime(self.timeRegionValue).tm_min)

			self.updateCaptureRange()


	def spinChanged(self):
		# Check if variables haven't already been processed by the spinboxes
		if self.slidersHaveBeenChanged==False:
			# Keep copy of old values incase new values exceed buffer time
			tempZoom = self.sampleTimeValue
			tempScroll = self.timeRegionValue

			# Update variables to new values
			self.sampleTimeValue=self.spinBoxDayZoom.value()*86400+self.spinBoxHrsZoom.value()*3600+self.spinBoxMinZoom.value()*60
			self.timeRegionValue=self.spinBoxDayScale.value()*86400+self.spinBoxHrsScale.value()*3600+self.spinBoxMinScale.value()*60

			# Check if new values exceed maximum buffer time
			if (self.sampleTimeValue > maximumTime):
				self.sampleTimeValue = tempZoom
				self.spinBoxDayZoom.setValue(time.gmtime(self.sampleTimeValue).tm_yday-1)
				self.spinBoxHrsZoom.setValue(time.gmtime(self.sampleTimeValue).tm_hour)
				self.spinBoxMinZoom.setValue(time.gmtime(self.sampleTimeValue).tm_min)
			if (self.timeRegionValue > maximumTime):
				self.timeRegionValue = tempScroll
				self.spinBoxDayScale.setValue(time.gmtime(self.timeRegionValue).tm_yday-1)
				self.spinBoxHrsScale.setValue(time.gmtime(self.timeRegionValue).tm_hour)
				self.spinBoxMinScale.setValue(time.gmtime(self.timeRegionValue).tm_min)

			# Set minumum range to 5 seconds not below 5
			if self.sampleTimeValue < 5:
				self.sampleTimeValue = 5

			# Re-adjust range of spectrum slider to cover the visible waterfall spectrum
			self.spectrumSlider.setRange(self.timeRegionValue, self.timeRegionValue + self.sampleTimeValue)

			# Get bottom stretch of the spectrogram data
			lastTimeValue = self.spectPlot.get_extent()
			[top, bottom] = self.spectAx.get_ylim()

			# Check if end of data is visible in spectrogram
			if (lastTimeValue[2]<bottom):
				# Prevent the horizontal slider from exceeding the end of data
				self.spectrumSlider.setRange(self.timeRegionValue, int(np.rint(lastTimeValue[2])))

			self.secondsToTime()
			# Update state
			self.slidersHaveBeenChanged=True

			# Adjust chart UI with new slider values.
			self.graphZoomSlider.setValue(self.sampleTimeValue)
			self.graphScrollSlider.setValue(self.timeRegionValue)

			self.updateCaptureRange()

	def secondsToTime(self, *fargs):
		# Update UI to represent new slider values
		if (int(time.strftime("%d",time.gmtime(self.sampleTimeValue)))-1) == 0:
			self.lowValue.setText(time.strftime("%H:%M:%S", time.gmtime(self.sampleTimeValue)))
		else:
			dayNo = int(time.strftime("%d",time.gmtime(self.sampleTimeValue)))-1
			self.lowValue.setText(str(dayNo)+' day - '+time.strftime("%H:%M:%S", time.gmtime(self.sampleTimeValue)))
		if (int(time.strftime("%d",time.gmtime(self.timeRegionValue)))-1) == 0:
			self.highValue.setText(time.strftime("%H:%M:%S", time.gmtime(self.timeRegionValue))+' ago')
		else:
			dayNo = int(time.strftime("%d",time.gmtime(self.timeRegionValue)))-1
			self.highValue.setText(str(dayNo)+' day and '+time.strftime("%H:%M:%S", time.gmtime(self.timeRegionValue))+' ago')


	def spectrumChanged(self):
		self.checkSpectrumSlider()
		# Store new spectrum number from the UI
		self.spectrumNumberScale = self.spectrumSlider.value()
		self.horizontalslidersHaveBeenChanged=True



	def checkSpectrumSlider(self):
		'''Check if new slider position exceeds the data on the spectrogram'''
		lastTimeValue = self.spectPlot.get_extent()
		[top, bottom] = self.spectAx.get_ylim()
		if(lastTimeValue[2] < top):
			# Ensure that the range of the spectrum slider does not exceed data size
			self.spectrumSlider.setRange(self.timeRegionValue, int(np.rint(lastTimeValue[2])))
		else:
			# Else let spectrum slider cover the colormap
			self.spectrumSlider.setRange(self.timeRegionValue, self.timeRegionValue + self.sampleTimeValue)

	def calibrate(self):
		# This is the variable that stores the height of the spectrum marker on the interface (black dashed line)
		self.horizontalMarker = 0
		# Reset poles
		self.initialize()

		if self.displayAverage:
			self.histAx.set_title('Frequency Spectrum (Average) - Pol %s' % self.pole)
			self.average_data = np.mean(self.data, axis = 0)
			histData = np.log(self.average_data)
			histData_dB = 10*np.log10(2**histData)
		else:
			# Create new horizontal line
			self.hline = self.spectAx.axhline(self.horizontalMarker, color='k', linestyle='--', linewidth=2)
			self.hline.set_ydata(0)
			spectrumMarkerRounded = int(np.rint(self.spectrumMarker))
			print(spectrumMarkerRounded)
			data = self.data[spectrumMarkerRounded]
			self.spectrumSlider.setValue(0)
		self.secondsToTime()

	def clear(self):
		self.data = np.delete(self.data, slice(0,self.num_rows), axis=0)
		self.spectPlot.set_extent([0,250,0,0])
		self.hline.set_ydata(0)

	def Averagecheckbox_toggled(self):
		if self.displayAverage:
			self.histAx.set_title('Frequency Spectrum - Pol %s' % self.pole)
			self.displayAverage=False
			self.horizontalslidersHaveBeenChanged=True	#Disable the spectrum slider
		else:
			self.displayAverage=True
			self.hline.set_ydata(0)
			extentValue = self.spectPlot.get_extent()
			[top, bottom] = self.spectAx.get_ylim()
			# If the end of the waterfall is visible, set the top to the end of the spectrum
			if(extentValue[2] < top):
				top = int(np.rint(extentValue[2]))
			# Scale to array indexes (snapboard_capture_time refers to the average storing time from SnapBoard)
			bottom = int(np.rint(bottom/snapboard_capture_time))
			# Scale to array indexes (snapboard_capture_time refers to the average storing time from SnapBoard)
			top = int(np.rint(top/snapboard_capture_time))
			# Get average from bottom to top of spectrogram
			self.average_data = np.mean(self.data[bottom:(top+1),:], axis = 0)
			histData = np.log(self.average_data)
			histData_dB = 10*np.log10(2**histData)
			self.histPlot.set_ydata(histData_dB)
			self.histAx.set_title('Frequency Spectrum (Average) - Pol %s' % self.pole)