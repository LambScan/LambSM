# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'interfaz.ui',
# licensing of 'interfaz.ui' applies.
#
# Created: Fri Oct 11 13:09:55 2019
#      by: pyside2-uic  running on PySide2 5.13.1
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1576, 820)
        MainWindow.setMinimumSize(QtCore.QSize(0, 0))
        MainWindow.setMaximumSize(QtCore.QSize(1660, 960))
        MainWindow.setCursor(QtCore.Qt.PointingHandCursor)
        self.graphicsView = QtWidgets.QGraphicsView(MainWindow)
        self.graphicsView.setGeometry(QtCore.QRect(-1, -1, 1581, 821))
        self.graphicsView.setFrameShape(QtWidgets.QFrame.WinPanel)
        self.graphicsView.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.graphicsView.setLineWidth(3)
        self.graphicsView.setMidLineWidth(-1)
        self.graphicsView.setRenderHints(QtGui.QPainter.Antialiasing|QtGui.QPainter.HighQualityAntialiasing|QtGui.QPainter.TextAntialiasing)
        self.graphicsView.setObjectName("graphicsView")

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "Form", None, -1))

