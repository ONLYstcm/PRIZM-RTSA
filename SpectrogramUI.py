# SpectrogramUI.py
# Code originally adapted from Tony DiCola (ton@dicola.com)
# http://www.github.com/tdicola/

from __future__ import division
import matplotlib
import time
import os
import matplotlib.pyplot as plt

from prizm_poles import is_non_zero_file, pol
from prizm_poles import maximumTime, spectrumCounter, isLocked, lockedPlotEvent, snapboard_capture_time

matplotlib.use('Qt5Agg')

from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.ticker import FuncFormatter
from PyQt5 import QtCore, QtGui, QtWidgets


VERSION = 'PRIZM Spectrogram v2.0'
# User interface for the PRIZM Spectrogram program.


# Current working directory
cwd = os.getcwd()
print(cwd)

# Objects for each pol
pol0 = pol('0', cwd, 'pol0.scio')
pol1 = pol('1', cwd, 'pol1.scio')

class SpectrogramCanvas(FigureCanvas):
	def __init__(self, window):
		"""Initialize spectrogram canvas graphs."""
		# Tell numpy to ignore errors like taking the log of 0
		#np.seterr(all='ignore')
		# Set up figure to hold plots
		self.figure = Figure(figsize=(1024,768), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0))
		# Initialize canvas
		super(SpectrogramCanvas, self).__init__(self.figure)

		gs = GridSpec(1, 2, left=0.07, right=0.95, bottom=0.06, top=0.95, wspace=0.05)
		#gs.tight_layout(self.figure)
		gs0 = GridSpecFromSubplotSpec(2, 2, subplot_spec=gs[0], height_ratios=[1,2], width_ratios=[9.5, 0.5])
		gs1 = GridSpecFromSubplotSpec(2, 2, subplot_spec=gs[1], height_ratios=[1,2], width_ratios=[9.5, 0.5])

		pol0.createFigure(self.figure, gs0)
		pol1.createFigure(self.figure, gs1)

		# Set up spectrogram color bar for the waterfall plot
		self.colourBar = self.figure.add_subplot(gs1[3])
		self.figure.colorbar(pol1.spectPlot, cax=self.colourBar, use_gridspec=True, format=FuncFormatter(lambda x, pos: '%d' % (x*100.0)))
		self.colourBar.set_ylabel('Intensity')

		msg = QtWidgets.QMessageBox()
		msg.setIcon(QtWidgets.QMessageBox.Critical)
		msg.setWindowTitle(".scio files missing")
		msg.setStandardButtons(QtWidgets.QMessageBox.Ok)

		# Show a message of which files are missing if files are missing
		if not is_non_zero_file('%s/pol0.scio' % cwd) and not is_non_zero_file('%s/pol1.scio' % cwd):
			msg.setText("Both pol0.scio and pol1.scio are missing. The interface will be enabled when the files are retrieved.")
			msg.exec_()
		if is_non_zero_file('%s/pol0.scio' % cwd) and not is_non_zero_file('%s/pol1.scio' % cwd):
			msg.setText("'pol1.scio' is missing.")
			msg.exec_()
		if not is_non_zero_file('%s/pol0.scio' % cwd) and is_non_zero_file('%s/pol1.scio' % cwd):
			msg.setText("'pol0.scio' is missing.")
			msg.exec_()

		# Functions that run in the background
		self.ani = FuncAnimation(self.figure, self._update, interval=2000, blit=False)
		self.updateAni = FuncAnimation(self.figure, self._updateAxis, interval=50, blit=False)


	def _update(self, *fargs):
		global spectrumCounter
		pol0.update()
		pol1.update()
		# Move to the next spectrum
		spectrumCounter = spectrumCounter + 1
		return (pol0.histPlot, pol0.spectPlot, pol1.histPlot, pol1.spectPlot)

	def _updateAxis(self, *fargs):
		pol0.updateAxis()
		pol1.updateAxis()

class MainWindow(QtWidgets.QMainWindow):
	def __init__(self):
		"""Set up the main window. This is the GUI components"""
		super(MainWindow, self).__init__()
		self.openDevice = None
		main = QtWidgets.QWidget()
		self.UI_Layout = self._setupMainLayout()
		main.setLayout(self.UI_Layout)
		self.enable = FuncAnimation(self.spectrogram.figure, self._enableUI, interval=500, blit=False)
		self.setCentralWidget(main)
		self.status = self.statusBar()
		self.setGeometry(10,10,900,600)
		self.setWindowTitle('PRIZM 100MHz Antenna')
		self.show()

	def updateStatus(self, message=''):
		"""Update the status bar of the window with the provided message text."""
		self.status.showMessage(message)

	def _setupMainLayout(self):
		global maximumTime
		self.controls = QtWidgets.QVBoxLayout()
		self.bufferControl = QtWidgets.QGroupBox('Total Time Buffer')
		self.bufferControl.setLayout(QtWidgets.QHBoxLayout())
		self.navigationControl = QtWidgets.QGroupBox()
		self.navigationControl.setLayout(QtWidgets.QHBoxLayout())

		self.spinBoxHour = QtWidgets.QSpinBox(value=0)
		self.spinBoxMinute = QtWidgets.QSpinBox(value=0)
		self.spinBoxDay = QtWidgets.QSpinBox(value=1)
		self.spinBoxDay.setRange(0,365)
		self.spinBoxMinute.setRange(0,59)
		self.spinBoxHour.setRange(0,23)
		self.spinBoxDay.valueChanged.connect(self.setMaximumTime)
		self.spinBoxMinute.valueChanged.connect(self.setMaximumTime)
		self.spinBoxHour.valueChanged.connect(self.setMaximumTime)

		self.bufferControl.layout().addWidget(QtWidgets.QLabel('Days:'), 1)
		self.bufferControl.layout().addWidget(self.spinBoxDay, 1)
		self.bufferControl.layout().addWidget(QtWidgets.QLabel('Hours:'), 1)
		self.bufferControl.layout().addWidget(self.spinBoxHour, 1)
		self.bufferControl.layout().addWidget(QtWidgets.QLabel('Minutes:'), 1)
		self.bufferControl.layout().addWidget(self.spinBoxMinute, 1)

		maximumTime = (86400*self.spinBoxDay.value()) + (3600*self.spinBoxHour.value()) + (60*self.spinBoxMinute.value())

		self.spectrogram = SpectrogramCanvas(self)
		self.navLocked = QtWidgets.QCheckBox("Lock Plot")
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

		self.calibrateBtn = QtWidgets.QPushButton('Calibrate Waterfall Spectrums of Pol 0 and Pol 1')
		self.calibrateBtn.clicked.connect(self._calibrateBtn)
		self.clearBtn = QtWidgets.QPushButton('Clear Waterfall Spectrums of Pol 0 and Pol 1')
		self.clearBtn.clicked.connect(self._clearBtn)

		self.controls.addWidget(self.calibrateBtn)
		self.controls.addWidget(self.clearBtn)
		self.controls.addStretch(1)

		layout = QtWidgets.QHBoxLayout()
		layout.addLayout(self.controls)
		layout.addWidget(self.spectrogram)

		# If any of the 'scio' files are missing disable the UI
		if not (pol0.has_been_initialised or pol1.has_been_initialised):
			self.bufferControl.setEnabled(False)
			self.polController.setEnabled(False)
			self.navigationControl.setEnabled(False)
			self.calibrateBtn.setEnabled(False)
			self.clearBtn.setEnabled(False)
		return layout

	def _enableUI(self, value):
		if pol0.has_been_initialised and pol1.has_been_initialised:	#Enable the UI when the 'scio' files are present
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
		global maximumTime

		pol0.initWidget()
		pol1.initWidget()

		pol0.secondsToTime()	# Set time text for pol0
		pol1.secondsToTime()	# Set time text for pol1

		tabsGraphsPols	= QtWidgets.QTabWidget()
		tabsGraphsPols.addTab(pol0.graphs,"Pol 0")
		tabsGraphsPols.addTab(pol1.graphs,"Pol 1")

		return (tabsGraphsPols)

	def Lockedcheckbox_toggled(self, value):
		global isLocked
		if isLocked:
			isLocked=False
		else:
			isLocked=True

	def _calibrateBtn(self):
		pol0.calibrate()
		pol1.calibrate()


	def _clearBtn(self):
		retval = self.showClearDataDialog()
		if(retval == QtWidgets.QMessageBox.Ok):
			pol0.clear()
			pol1.clear()

	def setMaximumTime(self):
		global maximumTime
		newTime = (86400*self.spinBoxDay.value()) + (3600*self.spinBoxHour.value()) + (60*self.spinBoxMinute.value())

		# Get the bottom of the spectrum on the waterfall plot. 'pol0.scio' and 'pol1.scio' should have the same number of spectrum
		lastTimeValue = pol0.spectPlot.get_extent()

		# If zero time is entered, reset to one day
		if newTime==0:
			maximumTime=86400
			self.spinBoxDay.setValue(1)
			self._zeroMaxTimeError()
		else:
			# If buffer time is shorter than the elapsed spectra time the show error
			if (newTime < lastTimeValue[2]):
				# If user accepts, cut off exceeding time
				retval = self.showMaxTimeDialog()
				if(retval == QtWidgets.QMessageBox.Ok):
					maximumTime = newTime
					pol0.graphScrollSlider.setRange(0, maximumTime)
					pol0.graphZoomSlider.setRange(5, maximumTime)
					pol0.spectrumSlider.setRange(pol0.timeRegionValue, pol0.timeRegionValue + pol0.sampleTimeValue)
					pol1.graphScrollSlider.setRange(0, maximumTime)
					pol1.graphZoomSlider.setRange(5, maximumTime)
					pol1.spectrumSlider.setRange(pol1.timeRegionValue, pol1.timeRegionValue + pol1.sampleTimeValue)
				# Else cancel
				else:
					self.spinBoxDay.setValue(time.gmtime(maximumTime).tm_yday-1)
					self.spinBoxHour.setValue(time.gmtime(maximumTime).tm_hour)
					self.spinBoxMinute.setValue(time.gmtime(maximumTime).tm_min)
			else:
				maximumTime = newTime
				# Update sliders to represent the new buffer time
				pol0.graphScrollSlider.setRange(0, maximumTime)
				pol0.graphZoomSlider.setRange(5, maximumTime)
				pol0.spectrumSlider.setRange(pol0.timeRegionValue, pol0.timeRegionValue + pol0.sampleTimeValue)
				pol1.graphScrollSlider.setRange(0, maximumTime)
				pol1.graphZoomSlider.setRange(5, maximumTime)
				pol1.spectrumSlider.setRange(pol1.timeRegionValue, pol1.timeRegionValue + pol1.sampleTimeValue)

	def showMaxTimeDialog(self):
		msg = QtWidgets.QMessageBox()
		msg.setIcon(QtWidgets.QMessageBox.Warning)
		msg.setText("Buffer time shorter than waterfall spectrum time")
		msg.setInformativeText("The buffer time you chose precedes the time used to capture spectrum data. Should you persist in with this buffer time, this will result in loss of the older data. Do you accept?")
		msg.setWindowTitle("Buffer Time Warning")
		msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
		return msg.exec_()

	def showClearDataDialog(self):
		msg = QtWidgets.QMessageBox()
		msg.setIcon(QtWidgets.QMessageBox.Warning)
		msg.setText("Clear capture data to release memory")
		msg.setInformativeText("Should you persist, this will result in loss of all the captured data. Do you accept?")
		msg.setWindowTitle("Clear Captured Data?")
		msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
		return msg.exec_()

	def _zeroMaxTimeError(self):
		msg = QtWidgets.QMessageBox()
		msg.setIcon(QtWidgets.QMessageBox.Information)
		msg.setWindowTitle("Invalid Buffer Time")
		msg.setText('Cannot have a zero buffer time')
		msg.exec_()
