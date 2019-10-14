from GUI.ui_mainwindow import *

from PySide2 import QtCore, QtGui, QtWidgets
import time


################################ Ventana Principal ######################################


#clase principal que representa la ventana principal de la aplicacion
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):


    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        self.setupUi(self)
        
        # inicializamos la grafica
        self.scene = QtWidgets.QGraphicsScene()
        self.graphicsView.setScene(self.scene)
        fondo = QtGui.QBrush(QtGui.QColor(255, 255, 255)) # background color
        self.graphicsView.setBackgroundBrush(fondo)

        #backgroud image
        background_image = QtGui.QPixmap()
        background_image.load("src/GUI/sm.png")
        background_item = self.scene.addPixmap(background_image)
        background_item.setPos(0,0)
        background_item.setZValue(-1)

        #inicializamos los elementos de la grafica
        boxPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 204, 0)), 7)
        exceptionBoxPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(255, 51, 0)), 7)

        #los elementos se encuentran agrupados en un diccionario
        self.objetos = {
        'init_box' : self.scene.addRect(0, 0, 180, 100, pen=boxPen),
        'start_streams_box' : self.scene.addRect(202, 204, 240, 131, pen=boxPen),
        'no_camera_box' : self.scene.addRect(500, 200, 192, 107, pen=exceptionBoxPen),
        'send_message_box' : self.scene.addRect(821, 202, 262, 108, pen=boxPen),
        'no_memory_box' : self.scene.addRect(1183, 183, 189, 103, pen=exceptionBoxPen),
        'end_box' : self.scene.addRect(1325, 0, 175, 98, pen=boxPen),
        'exit_box' : self.scene.addRect(843, 351, 172, 73, pen=boxPen),
        'get_frames_box' : self.scene.addRect(511, 503, 263, 118, pen=boxPen),
        'processing_and_filter_box' : self.scene.addRect(924, 497, 238, 131, pen=boxPen),
        'save_box' : self.scene.addRect(961, 651, 174, 83, pen=boxPen),
        'lamb_scan_box' : self.scene.addRect(157, 118, 1234, 649, pen=boxPen)
        }

        #ocultamos todos los elementos
        for key in self.objetos:
            self.objetos[key].hide()


############################       Util       ############################

    def refresh(self):
        '''
        Actualiza la grafica para que se muestren los cambios.
        :return:
        '''
        QtCore.QCoreApplication.processEvents()
        time.sleep(0.5)





############################   State Machine   ############################
    def to_init_state(self):
        '''
        Resalta en la grafica el estado Init.
        :return:
        '''
        self.objetos['init_box'].show()
        self.refresh()

    def init_to_lamb_scan(self):
        '''
        Resalta en la grafica el estado LambScan, ocultando el estado Init
        :return:
        '''
        self.objetos['init_box'].hide()
        self.objetos['lamb_scan_box'].show()
        self.refresh()

    def lamb_scan_to_end(self):
        '''
        Resalta en la grafica el estado End, ocultando el estado LambScan
        :return:
        '''
        self.objetos['lamb_scan_box'].hide()
        self.objetos['end_box'].show()
        self.refresh()




############################  Sub-State Machine  ############################
    def to_start_streams_state(self):
        '''
        Resalta en la grafica el estado StartStreams
        :return:
        '''
        self.objetos['start_streams_box'].show()
        self.refresh()


    def start_streams_to_get_frames(self):
        '''
        Resalta en la grafica el estado GetFrames, ocultando el estado StartStreams
        :return:
        '''
        self.objetos['start_streams_box'].hide()
        self.objetos['get_frames_box'].show()
        self.refresh()


    def get_frames_to_processing_and_filter(self):
        '''
        Resalta en la grafica el estado ProcessingAndFilter, ocultando el estado GetFrames
        :return:
        '''
        self.objetos['get_frames_box'].hide()
        self.objetos['processing_and_filter_box'].show()
        self.refresh()


    def processing_and_filter_to_get_frames(self):
        '''
        Resalta en la grafica el estado ProcessingAndFilter, ocultando el estado GetFrames
        :return:
        '''
        self.objetos['processing_and_filter_box'].hide()
        self.objetos['get_frames_box'].show()
        self.refresh()


    def processing_and_filter_to_save(self):
        '''
        Resalta en la grafica el estado Save, ocultando el estado ProcessingAndFilter
        :return:
        '''
        self.objetos['processing_and_filter_box'].hide()
        self.objetos['save_box'].show()
        self.refresh()


    def save_to_get_frames(self):
        '''
        Resalta en la grafica el estado GetFrames, ocultando el estado Save
        :return:
        '''
        self.objetos['save_box'].hide()
        self.objetos['get_frames_box'].show()
        self.refresh()


    def get_frames_to_exit(self):
        '''
        Resalta en la grafica el estado GetFrames, ocultando el estado Save
        :return:
        '''
        self.objetos['get_frames_box'].hide()
        self.objetos['exit_box'].show()
        self.refresh()


    def out_of_exit_state(self):
        '''
        Resalta en la grafica el estado GetFrames, ocultando el estado Save
        :return:
        '''
        self.objetos['exit_box'].hide()
        self.refresh()



############################     Exceptions     ############################

    def start_streams_to_no_camera(self):
        '''
        Resalta en la grafica el estado NoCamera, ocultando el estado StartStreams
        :return:
        '''
        self.objetos['start_streams_box'].hide()
        self.objetos['no_camera_box'].show()
        self.refresh()


    def get_frames_to_no_camera(self):
        '''
        Resalta en la grafica el estado NoCamera, ocultando el estado StartStreams
        :return:
        '''
        self.objetos['get_frames_box'].hide()
        self.objetos['no_camera_box'].show()
        self.refresh()


    def no_camera_to_start_streams(self):
        '''
        Resalta en la grafica el estado GetFrames, ocultando el estado Save
        :return:
        '''
        self.objetos['no_camera_box'].hide()
        self.objetos['start_streams_box'].show()
        self.refresh()


    def save_to_no_memory(self):
        '''
        Resalta en la grafica el estado GetFrames, ocultando el estado Save
        :return:
        '''
        self.objetos['save_box'].hide()
        self.objetos['no_memory_box'].show()
        self.refresh()


    def no_memory_to_save(self):
        '''
        Resalta en la grafica el estado GetFrames, ocultando el estado Save
        :return:
        '''
        self.objetos['no_memory_box'].hide()
        self.objetos['save_box'].show()
        self.refresh()


    def no_memory_to_send_message(self):
        '''
        Resalta en la grafica el estado GetFrames, ocultando el estado Save
        :return:
        '''
        self.objetos['no_memory_box'].hide()
        self.objetos['send_message_box'].show()
        self.refresh()


    def no_camera_to_send_message(self):
        '''
        Resalta en la grafica el estado GetFrames, ocultando el estado Save
        :return:
        '''
        self.objetos['no_camera_box'].hide()
        self.objetos['send_message_box'].show()
        self.refresh()


    def send_message_to_exit(self):
        '''
        Resalta en la grafica el estado GetFrames, ocultando el estado Save
        :return:
        '''
        self.objetos['send_message_box'].hide()
        self.objetos['exit_box'].show()
        self.refresh()









