#!/usr/bin/python3
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
#

from genericworker import *

# If RoboComp was compiled with Python bindings you can use InnerModel in Python
# sys.path.append('/opt/robocomp/lib')
# import librobocomp_qmat
# import librobocomp_osgviewer
# import librobocomp_innermodel
from FileManager import save_frames, FileManager
from PySide2 import QtCore
from rs_camera import RSCamera
from lamb_filter import isThereALamb
import signal



class SpecificWorker(GenericWorker):
	def __init__(self, proxy_map):
		super(SpecificWorker, self).__init__(proxy_map)
		self.exit = False
		self.no_cam = 0
		self.no_memory = 0
		self.Period = 1000  # 1 second for frame
		self.Saver_period = 1000 * 60 * 25  # 25 min for a random picture
		self.saver_timer = QtCore.QTimer(self)
		self.timer.setInterval(self.Period)
		self.timer.setSingleShot(True)
		self.saver_timer.setInterval(self.Saver_period)
		self.saver_timer.setSingleShot(True)

		self.camera = None
		self.lamb_path = ""
		self.frame = (None, None)

		self.mainwindow = 0

		self.Application.start()

	def receive_signal(self, signum, stack):
		print("\n\n\t[eCtrl + C]\n\n")
		self.exit = True

	def __del__(self):
		print('SpecificWorker destructor')

	def setParams(self, params):
		self.mainwindow = params
		return True

	# =============== Slots methods for State Machine ===================
	# ===================================================================
	#
	# sm_init
	#
	@QtCore.Slot()
	def sm_init(self):
		print("Entered state init")
		self.mainwindow.to_init_state()

		signal.signal(signal.SIGINT, self.receive_signal)
		self.t_init_to_lambscan.emit()

	#
	# sm_lambscan
	#
	@QtCore.Slot()
	def sm_lambscan(self):
		print("Entered state lambscan")
		self.mainwindow.init_to_lamb_scan()


	#
	# sm_end
	#
	@QtCore.Slot()
	def sm_end(self):
		print("Entered state end")
		self.mainwindow.lamb_scan_to_end()

		from PySide2.QtWidgets import QApplication
		QApplication.quit()

	#
	# sm_start_streams
	#
	@QtCore.Slot()
	def sm_start_streams(self):
		print("Entered state start_streams")
		self.mainwindow.to_start_streams_state()
		try:
			self.camera = RSCamera()
			if self.camera.start():
				self.saver_timer.start()
				self.mainwindow.start_streams_to_get_frames()
				self.t_start_streams_to_get_frames.emit()
			else:
				raise Exception("It couldn't start the streams")
		except Exception as e:
			print("problem starting the streams of the camera\n", e)
			self.mainwindow.start_streams_to_no_camera()
			self.t_start_streams_to_no_camera.emit()

	#
	# sm_get_frames
	#
	@QtCore.Slot()
	def sm_get_frames(self):
		print("Entered state get_frames")
		if self.exit:
			print("\n\n\t[!] Ctrl + C received. Closing program...\n\n")
			self.mainwindow.get_frames_to_exit()
			self.t_get_frames_to_exit.emit()
		else:
			self.timer.start()
			try:
				while self.timer.remainingTime() > 0:
					self.frame = self.camera.get_frame()
				# self.timer.stop()
				self.mainwindow.get_frames_to_processing_and_filter()
				self.t_get_frames_to_processing_and_filter.emit()
			except Exception as e:
				# TODO: comprobar si esto funciona. Cuando desconectas la camara, salta una excepcion en vez de entrar aqui.
				print("An error occur when taking a new frame,:\n " + str(e))
				print(type(e))
				self.mainwindow.get_frames_to_no_camera()
				self.t_get_frames_to_no_camera.emit()

	#
	# sm_no_camera
	#
	@QtCore.Slot()
	def sm_no_camera(self):
		print("Entered state no_camera")
		self.camera.__del__()
		self.camera = None
		self.no_cam += 1
		if self.no_cam > 2:
			self.mainwindow.no_camera_to_send_message()
			self.t_no_camera_to_send_message.emit()
		else:
			self.mainwindow.no_camera_to_start_streams()
			self.t_no_camera_to_start_streams.emit()

	#
	# sm_no_memory
	#
	@QtCore.Slot()
	def sm_no_memory(self):
		print("Entered state no_memory")
		self.no_memory += 1
		if self.no_memory > 2:
			self.mainwindow.no_memory_to_send_message()
			self.t_no_memory_to_send_message.emit()
		else:
			self.mainwindow.no_memory_to_save()
			self.t_no_memory_to_save.emit()

	#
	# sm_processing_and_filter
	#
	@QtCore.Slot()
	def sm_processing_and_filter(self):
		print("Entered state processing_and_filter")
		self.no_cam = 0
		isLamb, self.lamb_path = isThereALamb(*self.frame)
		if isLamb or self.saver_timer.remainingTime() == 0:
			self.mainwindow.processing_and_filter_to_save()
			self.t_processing_and_filter_to_save.emit()
		else:
			self.mainwindow.processing_and_filter_to_get_frames()
			self.t_processing_and_filter_to_get_frames.emit()

	#
	# sm_save
	#
	@QtCore.Slot()
	def sm_save(self):
		print("Entered state save")
		try:
			save_frames(*self.frame, self.lamb_path)
			self.saver_timer.start()
			self.mainwindow.save_to_get_frames()
			self.t_save_to_get_frames.emit()
		except FileManager as e:
			print(("Problem saving the file\n", e))
			self.mainwindow.save_to_no_memory()
			self.t_save_to_no_memory.emit()

	#
	# sm_send_message
	#
	@QtCore.Slot()
	def sm_send_message(self):
		print("Entered state send_message")
		print("- Not implemented yet, send an email to the developers.")
		self.mainwindow.send_message_to_exit()
		self.t_send_message_to_exit.emit()

	#
	# sm_exit
	#
	@QtCore.Slot()
	def sm_exit(self):
		print("Entered state exit")
		if self.camera is not None:
			self.camera.__del__()
		self.mainwindow.out_of_exit_state()
		self.t_lambscan_to_end.emit()

# =================================================================
# =================================================================
