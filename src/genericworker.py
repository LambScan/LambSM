#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 by YOUR NAME HERE
#
#    This file is part of RoboComp
#
#    RoboComp is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RoboComp is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.

import sys, Ice, os
from PySide2 import QtWidgets, QtCore

ROBOCOMP = ''
try:
	ROBOCOMP = os.environ['ROBOCOMP']
except KeyError:
	print('$ROBOCOMP environment variable not set, using the default value /opt/robocomp')
	ROBOCOMP = '/opt/robocomp'

preStr = "-I/opt/robocomp/interfaces/ -I"+ROBOCOMP+"/interfaces/ --all /opt/robocomp/interfaces/"
Ice.loadSlice(preStr+"CommonBehavior.ice")
import RoboCompCommonBehavior

additionalPathStr = ''
icePaths = [ '/opt/robocomp/interfaces' ]
try:
	SLICE_PATH = os.environ['SLICE_PATH'].split(':')
	for p in SLICE_PATH:
		icePaths.append(p)
		additionalPathStr += ' -I' + p + ' '
	icePaths.append('/opt/robocomp/interfaces')
except:
	print('SLICE_PATH environment variable was not exported. Using only the default paths')
	pass





class GenericWorker(QtCore.QObject):

	kill = QtCore.Signal()
#Signals for State Machine
	startingtocomponent = QtCore.Signal()
	startingtoload_image = QtCore.Signal()
	startingtowatch_live = QtCore.Signal()
	startingtoexception_handler = QtCore.Signal()
	startingtothe_end = QtCore.Signal()
	componenttostarting = QtCore.Signal()
	componenttoexception_handler = QtCore.Signal()
	componenttothe_end = QtCore.Signal()
	load_imagetostarting = QtCore.Signal()
	load_imagetoexception_handler = QtCore.Signal()
	load_imagetothe_end = QtCore.Signal()
	watch_livetostarting = QtCore.Signal()
	watch_livetoexception_handler = QtCore.Signal()
	watch_livetothe_end = QtCore.Signal()
	exception_handlertostarting = QtCore.Signal()
	exception_handlertocomponent = QtCore.Signal()
	exception_handlertoload_image = QtCore.Signal()
	exception_handlertowatch_live = QtCore.Signal()
	load_streamstoget_frames = QtCore.Signal()
	get_framestosave_frames = QtCore.Signal()
	get_framestoclose = QtCore.Signal()
	save_framestoget_frames = QtCore.Signal()

#-------------------------

	def __init__(self, mprx):
		super(GenericWorker, self).__init__()



		
		self.mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
		self.Period = 30
		self.timer = QtCore.QTimer(self)

#State Machine
		self.global_machine= QtCore.QStateMachine()
		self.component_state = QtCore.QState(self.global_machine)
		self.load_image_state = QtCore.QState(self.global_machine)
		self.watch_live_state = QtCore.QState(self.global_machine)
		self.exception_handler_state = QtCore.QState(self.global_machine)
		self.starting_state = QtCore.QState(self.global_machine)

		self.the_end_state = QtCore.QFinalState(self.global_machine)



		self.get_frames_state = QtCore.QState(self.watch_live_state)
		self.save_frames_state = QtCore.QState(self.watch_live_state)
		self.load_streams_state = QtCore.QState(self.watch_live_state)

		self.close_state = QtCore.QFinalState(self.watch_live_state)


#------------------
#Initialization State machine
		self.starting_state.addTransition(self.startingtocomponent, self.component_state)
		self.starting_state.addTransition(self.startingtoload_image, self.load_image_state)
		self.starting_state.addTransition(self.startingtowatch_live, self.watch_live_state)
		self.starting_state.addTransition(self.startingtoexception_handler, self.exception_handler_state)
		self.starting_state.addTransition(self.startingtothe_end, self.the_end_state)
		self.component_state.addTransition(self.componenttostarting, self.starting_state)
		self.component_state.addTransition(self.componenttoexception_handler, self.exception_handler_state)
		self.component_state.addTransition(self.componenttothe_end, self.the_end_state)
		self.load_image_state.addTransition(self.load_imagetostarting, self.starting_state)
		self.load_image_state.addTransition(self.load_imagetoexception_handler, self.exception_handler_state)
		self.load_image_state.addTransition(self.load_imagetothe_end, self.the_end_state)
		self.watch_live_state.addTransition(self.watch_livetostarting, self.starting_state)
		self.watch_live_state.addTransition(self.watch_livetoexception_handler, self.exception_handler_state)
		self.watch_live_state.addTransition(self.watch_livetothe_end, self.the_end_state)
		self.exception_handler_state.addTransition(self.exception_handlertostarting, self.starting_state)
		self.exception_handler_state.addTransition(self.exception_handlertocomponent, self.component_state)
		self.exception_handler_state.addTransition(self.exception_handlertoload_image, self.load_image_state)
		self.exception_handler_state.addTransition(self.exception_handlertowatch_live, self.watch_live_state)
		self.load_streams_state.addTransition(self.load_streamstoget_frames, self.get_frames_state)
		self.get_frames_state.addTransition(self.get_framestosave_frames, self.save_frames_state)
		self.get_frames_state.addTransition(self.get_framestoclose, self.close_state)
		self.save_frames_state.addTransition(self.save_framestoget_frames, self.get_frames_state)


		self.component_state.entered.connect(self.sm_component)
		self.load_image_state.entered.connect(self.sm_load_image)
		self.watch_live_state.entered.connect(self.sm_watch_live)
		self.exception_handler_state.entered.connect(self.sm_exception_handler)
		self.starting_state.entered.connect(self.sm_starting)
		self.the_end_state.entered.connect(self.sm_the_end)
		self.load_streams_state.entered.connect(self.sm_load_streams)
		self.close_state.entered.connect(self.sm_close)
		self.get_frames_state.entered.connect(self.sm_get_frames)
		self.save_frames_state.entered.connect(self.sm_save_frames)

		self.global_machine.setInitialState(self.starting_state)
		self.watch_live_state.setInitialState(self.load_streams_state)

#------------------

#Slots funtion State Machine
	@QtCore.Slot()
	def sm_component(self):
		print("Error: lack sm_component in Specificworker")
		sys.exit(-1)

	@QtCore.Slot()
	def sm_load_image(self):
		print("Error: lack sm_load_image in Specificworker")
		sys.exit(-1)

	@QtCore.Slot()
	def sm_watch_live(self):
		print("Error: lack sm_watch_live in Specificworker")
		sys.exit(-1)

	@QtCore.Slot()
	def sm_exception_handler(self):
		print("Error: lack sm_exception_handler in Specificworker")
		sys.exit(-1)

	@QtCore.Slot()
	def sm_starting(self):
		print("Error: lack sm_starting in Specificworker")
		sys.exit(-1)

	@QtCore.Slot()
	def sm_the_end(self):
		print("Error: lack sm_the_end in Specificworker")
		sys.exit(-1)

	@QtCore.Slot()
	def sm_get_frames(self):
		print("Error: lack sm_get_frames in Specificworker")
		sys.exit(-1)

	@QtCore.Slot()
	def sm_save_frames(self):
		print("Error: lack sm_save_frames in Specificworker")
		sys.exit(-1)

	@QtCore.Slot()
	def sm_load_streams(self):
		print("Error: lack sm_load_streams in Specificworker")
		sys.exit(-1)

	@QtCore.Slot()
	def sm_close(self):
		print("Error: lack sm_close in Specificworker")
		sys.exit(-1)


#-------------------------
	@QtCore.Slot()
	def killYourSelf(self):
		rDebug("Killing myself")
		self.kill.emit()

	# \brief Change compute period
	# @param per Period in ms
	@QtCore.Slot(int)
	def setPeriod(self, p):
		print("Period changed", p)
		Period = p
		timer.start(Period)
