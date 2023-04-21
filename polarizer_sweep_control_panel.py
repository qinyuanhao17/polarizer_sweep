import sys
import time
import clr
import nidaqmx

import polarizer_sweep_ui
from threading import Thread
from PyQt5.QtGui import QIcon, QPixmap, QCursor, QMouseEvent, QColor, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QEvent
from PyQt5.QtWidgets import QWidget, QApplication, QGraphicsDropShadowEffect,QDesktopWidget, QFileDialog, QVBoxLayout, QMessageBox

# Write in file paths of dlls needed. 
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.IntegratedStepperMotorsCLI.dll")

# Import functions from dlls. 
from Thorlabs.MotionControl import DeviceManagerCLI
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import MotorDirection
from Thorlabs.MotionControl.IntegratedStepperMotorsCLI import *
from Thorlabs.MotionControl.IntegratedStepperMotorsCLI import CageRotator
from System import Decimal 

class MyWindow(polarizer_sweep_ui.Ui_Form, QWidget):
    rotator_a_info = pyqtSignal(str)
    rotator_a_progress_bar_info = pyqtSignal(float)
    rotator_b_info = pyqtSignal(str)
    rotator_b_progress_bar_info = pyqtSignal(float)
    def __init__(self):

        super().__init__()
        
        # init UI
        self.setupUi(self)
        self.ui_width = int(QDesktopWidget().availableGeometry().size().width()*0.65)
        self.ui_height = int(QDesktopWidget().availableGeometry().size().height()*0.65)
        self.resize(self.ui_width, self.ui_height)
        center_pointer = QDesktopWidget().availableGeometry().center()
        x = center_pointer.x()
        y = center_pointer.y()
        old_x, old_y, width, height = self.frameGeometry().getRect()
        self.move(int(x - width / 2), int(y - height / 2))

        # set flag off and widget translucent
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # set window blur
        self.render_shadow()
        
        # init window button signal
        self.window_btn_signal()

        # init rotator A signal
        self.rotator_a_signal()
        # init rotator A info ui
        self.rotator_a_info_ui()

        # connect and set when boot
        self.connect_thread()
        # self.rotator_a_velocity_acceleration_step_set()
        # init rotator B signal
        # self.rotator_b_signal()
        # # init rotator B info ui
        # self.rotator_b_info_ui()

        # # connect and set when boot
        # self.b_connect_thread()
        # # self.rotator_a_velocity_acceleration_step_set()
        
        
    '''Set Rotator A'''
    def rotator_a_signal(self):
        self.rotator_a_connect_btn.clicked.connect(self.rotator_connect)

        #message signal
        self.rotator_a_info.connect(self.rotator_a_slot)
        self.rotator_a_progress_bar_info.connect(self.rotator_a_progress_bar_thread)
        # scroll area scrollbar signal
        self.rot_a_scroll.verticalScrollBar().rangeChanged.connect(
            lambda: self.rot_a_scroll.verticalScrollBar().setValue(
                self.rot_a_scroll.verticalScrollBar().maximum()
            )
        )
        # Home button signal
        self.home_tbtn.clicked.connect(self.rotator_a_home)
        # Disconnect button signal
        self.disconnect_btn.clicked.connect(self.rotator_a_disconnect)
        # move to signal
        self.move_tbtn.clicked.connect(self.rotator_a_move_to_position)
        self.rot_a_ledit.returnPressed.connect(self.rotator_a_move_to_position)
        # stop signal
        self.stop_tbtn.clicked.connect(self.rotator_a_stop)
        # drive signal
        self.rotator_a_set_btn.clicked.connect(self.rotator_a_velocity_acceleration_step_set)
        self.rotator_a_forward_btn.clicked.connect(self.rotator_a_step_forward)
        self.rotator_a_backward_btn.clicked.connect(self.rotator_a_step_backward)
        self.rotator_a_forward_btn.pressed.connect(self.rotator_a_continuous_forward_pressed)
        self.rotator_a_backward_btn.pressed.connect(self.rotator_a_continuous_backward_pressed)
        self.rotator_a_forward_btn.released.connect(self.rotator_a_continuous_released)
        self.rotator_a_backward_btn.released.connect(self.rotator_a_continuous_released)

        # Polarization sweep signal
        self.rotator_a_sweep_start_btn.clicked.connect(self.polarization_sweep)
        self.rotator_a_interrupt_btn.clicked.connect(self.rotator_a_stop_sweep)
        # frame calculation signal
        self.rotator_a_calc_btn.clicked.connect(self.rotator_a_frame_calc)
    def rotator_a_stop_sweep(self):
        self.__stopConstant = True
    def connect_thread(self):
        boot_thread = Thread(
            target=self.rotator_connect
        )
        boot_thread.start()

    def rotator_connect(self):
        serial_number = self.rotator_a_serial_cbox.currentText().strip('S/N ')
        # Init rotator A self.device_a
        DeviceManagerCLI.BuildDeviceList()
        self.device_a = CageRotator.CreateCageRotator(serial_number)
        self.device_a.Connect(serial_number)
        rtn = self.device_a.IsConnected
        if rtn:
             self.rotator_a_info.emit('Rotator A is connected')
        # Ensure that the self.device_a settings have been initialized.
        if not self.device_a.IsSettingsInitialized():
            self.device_a.WaitForSettingsInitialized(3000)  # 3 second timeout.
            assert self.device_a.IsSettingsInitialized() is True

        # Start polling loop and enable self.device_a.
        polling_rate = 250
        self.device_a.StartPolling(polling_rate)  #250ms polling rate.
        self.rotator_a_info.emit('Polling rate: {}'.format(polling_rate))
        self.device_a.EnableDevice()
        time.sleep(0.25)  # Wait for self.device_a to enable.

        # Get Device Information and display description.
        device_info = self.device_a.GetDeviceInfo()
        self.rotator_a_info.emit('{}: {}'.format(device_info.Description,self.rotator_a_serial_cbox.currentText()))
        self.rotator_a_info.emit('-'*60)
        # Load any configuration settings needed by the controller/stage.
        self.device_a.LoadMotorConfiguration(serial_number, DeviceConfiguration.DeviceSettingsUseOptionType.UseDeviceSettings)
        self.device_a.LoadMotorConfiguration(serial_number)
        thread = Thread(
            target=self.rotator_a_position_view
        )
        thread.start()
        
    def rotator_a_home(self):
        if self.device_a.Status.IsHoming:
            pass
        else:
            self.rotator_a_info.emit('Rotator A is homimg, please wait.')
            thread = Thread(
                target = self.rotator_a_home_thread
            )
            thread.start()
        
    def rotator_a_home_thread(self):
       
        
        if self.device_a.IsConnected:
            workDone = self.device_a.InitializeWaitHandler()

            self.device_a.Home(workDone)
            
            if self.device_a.Status.IsHomed:
                self.rotator_a_info.emit('Rotator A is homed.')
                self.rotator_a_info.emit('-'*60)
                
        else:
            self.rotator_a_info.emit('Device is not connected.')
            self.rotator_a_info.emit('-'*60)
        
    def rotator_a_disconnect(self):
        self.device_a.StopPolling()
        self.device_a.Disconnect(True)
        if not self.device_a.IsConnected:
            self.rotator_a_info.emit('Rotator A is disconnected.')
            self.rotator_a_info.emit('-'*60)
    def rotator_a_position_view(self):
        
        self.position_view.setSmallDecimalPoint(True)
        while True:
            if self.device_a.IsConnected:

                self.position_view.display(float(str(self.device_a.Position)))
                time.sleep(0.2)
            else:
                break
    def rotator_a_move_to_position(self):
        
        velPars = self.device_a.GetVelocityParams()
        velPars.MaxVelocity = Decimal(15)
        self.device_a.SetVelocityParams(velPars)

        new_position = Decimal(float(self.rot_a_ledit.text()))
        workDone = self.device_a.InitializeWaitHandler()
        self.device_a.MoveTo(new_position, workDone)
        self.rot_a_ledit.clear()
    def rotator_a_stop(self):
        self.device_a.StopImmediate()
    def rotator_a_velocity_acceleration_step_set(self):
        
        new_velocity = Decimal(int(self.rotator_a_velocity_spbx.text()))
        new_acceleration = Decimal(int(self.rotator_a_acceleration_spbx.text()))
        new_step = Decimal(float(self.rotator_a_step_spbx.text()))
        velPars = self.device_a.GetVelocityParams()
        velPars.MaxVelocity = new_velocity
        velPars.Acceleration = new_acceleration
        
        self.device_a.SetVelocityParams(velPars)
        
        self.device_a.SetVelocityParams(velPars)


        self.rotator_a_info.emit('Velocity: {}'.format(new_velocity))
        self.rotator_a_info.emit('Acceleration: {}'.format(new_acceleration))
        self.rotator_a_info.emit('Step: {}'.format(new_step))
        self.rotator_a_info.emit('-'*60)
    def rotator_a_step_forward(self):
        if self.device_a.Status.IsInMotion:
            pass
        else:
            if self.rotator_a_stp_rdbtn.isChecked():
                step = Decimal(float(self.rotator_a_step_spbx.text()))
                current_position = self.device_a.Position
                new_position = current_position + step
                workDone = self.device_a.InitializeWaitHandler()
                self.device_a.MoveTo(new_position, workDone)
                
            elif self.rotator_a_cont_rdbtn.isChecked():
                pass
    def rotator_a_step_backward(self):
        if self.device_a.Status.IsInMotion:
            pass
        else:
            if self.rotator_a_stp_rdbtn.isChecked():
                step = Decimal(float(self.rotator_a_step_spbx.text()))
                current_position = self.device_a.Position
                new_position = current_position - step
                workDone = self.device_a.InitializeWaitHandler()
                if float(str(new_position)) >= 0:
                    self.device_a.MoveTo(new_position, workDone)
                elif float(str(new_position)) < 0:
                    new_position = Decimal(new_position+360)
                    self.device_a.MoveTo(new_position, workDone)
                
            elif self.rotator_a_cont_rdbtn.isChecked():
                pass
    def rotator_a_continuous_forward_pressed(self):
        if self.rotator_a_stp_rdbtn.isChecked():
            pass
        elif self.rotator_a_cont_rdbtn.isChecked():
            new_direction_forward = MotorDirection.Forward 
            self.device_a.MoveContinuous(MotorDirection.Forward)
    def rotator_a_continuous_backward_pressed(self):
        if self.rotator_a_stp_rdbtn.isChecked():
            pass
        elif self.rotator_a_cont_rdbtn.isChecked():
            new_direction_forward = MotorDirection.Backward 
            self.device_a.MoveContinuous(MotorDirection.Backward)
    
    def rotator_a_continuous_released(self):
        self.device_a.StopImmediate()

    ''' Polarization Sweep'''
    def polarization_sweep(self):
        self.thread_read_write = Thread(
            target= self.rotator_a_read_write_thread
        )
        self.thread_read_write.start()
    def rotator_a_progress_bar_thread(self,msg):
        self.rotato_a_progressbar.setValue(int(msg))
    def rotator_a_frame_calc(self):
        a_start_position = float(self.rotator_a_startpos_spbx.text())
        a_stop_position = float(self.rotator_a_stoppos_spbx.text())
        a_step = float(self.rotator_a_sweepstep_spbx.text())
        a_stime = float(self.rotator_a_stime_spbx.text())
        tot_frame = int((a_stop_position - a_start_position)/a_step+1)
        new_position = Decimal(a_start_position)
        workDone = self.device_a.InitializeWaitHandler()
        self.device_a.MoveTo(new_position, workDone)
        time.sleep(0.5)
        if self.device_a.IsConnected:
            self.rotator_a_frame_spbx.setValue(tot_frame)    
            
    def rotator_a_read_write_thread(self):
        
        a_start_position = float(self.rotator_a_startpos_spbx.text())
        a_stop_position = float(self.rotator_a_stoppos_spbx.text())
        a_step = float(self.rotator_a_sweepstep_spbx.text())
        a_stime = float(self.rotator_a_stime_spbx.text())
        tot_frame = int((a_stop_position - a_start_position)/a_step+1)

        with nidaqmx.Task() as read_task, nidaqmx.Task() as write_task:
    
            di = read_task.di_channels.add_di_chan("Dev1/port0/line1")
            do = write_task.do_channels.add_do_chan("Dev1/port0/line0")           
            
            i = 0
            self.__stopConstant = False
            while i < (tot_frame+1):
                
                if self.__stopConstant == False:
                    self.rotator_a_progress_bar_info.emit(i/tot_frame*100)
                    if self.device_a.IsConnected:
                        data = read_task.read()
                        if  data == False:    
                            write_task.write(True)
                            time.sleep(0.01)
                            write_task.write(False)
                            time.sleep(a_stime+2)             
                            self.rotator_a_info.emit('{}'.format(i))
                            if i == tot_frame:
                                pass 
                            else:
                                current_position = self.device_a.Position
                                new_position = current_position + Decimal(a_step)
                                workDone = self.device_a.InitializeWaitHandler()
                                self.device_a.MoveTo(new_position, workDone)
                                time.sleep(0.5)
                                while True:
                                    if self.device_a.Status.IsInMotion:
                                        time.sleep(0.01)
                                    else:
                                        break                          
                            i += 1
                            
                    else:
                        break            
                else:
                    break                    
    '''Set Rotator A info ui'''
    def rotator_a_info_ui(self):

        self.rot_a_msg.setWordWrap(True)  # 自动换行
        self.rot_a_msg.setAlignment(Qt.AlignTop)  # 靠上

        # 用于存放消息
        self.rot_a_msg_history = []

    def rotator_a_slot(self, msg):

        self.rot_a_msg_history.append(msg)
        self.rot_a_msg.setText("<br>".join(self.rot_a_msg_history))
        self.rot_a_msg.resize(400, self.rot_a_msg.frameSize().height() + 20)
        self.rot_a_msg.repaint()  # 更新内容，如果不更新可能没有显示新内容


            
    '''Set window ui'''
    def window_btn_signal(self):
        # window button sigmal
        self.close_btn.clicked.connect(self.close)
        self.max_btn.clicked.connect(self.maxornorm)
        self.min_btn.clicked.connect(self.showMinimized)
        
    #create window blur
    def render_shadow(self):
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setOffset(0, 0)  # 偏移
        self.shadow.setBlurRadius(30)  # 阴影半径
        self.shadow.setColor(QColor(128, 128, 255))  # 阴影颜色
        self.mainwidget.setGraphicsEffect(self.shadow)  # 将设置套用到widget窗口中

    def maxornorm(self):
        if self.isMaximized():
            self.showNormal()
            self.norm_icon = QIcon()
            self.norm_icon.addPixmap(QPixmap(":/my_icons/images/icons/max.svg"), QIcon.Normal, QIcon.Off)
            self.max_btn.setIcon(self.norm_icon)
        else:
            self.showMaximized()
            self.max_icon = QIcon()
            self.max_icon.addPixmap(QPixmap(":/my_icons/images/icons/norm.svg"), QIcon.Normal, QIcon.Off)
            self.max_btn.setIcon(self.max_icon)

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:
            self.m_flag = True
            self.m_Position = QPoint
            self.m_Position = event.globalPos() - self.pos()  # 获取鼠标相对窗口的位置
            event.accept()
            self.setCursor(QCursor(Qt.OpenHandCursor))  # 更改鼠标图标
        
    def mouseMoveEvent(self, QMouseEvent):
        m_position = QPoint
        m_position = QMouseEvent.globalPos() - self.pos()
        width = QDesktopWidget().availableGeometry().size().width()
        height = QDesktopWidget().availableGeometry().size().height()
        if m_position.x() < width*0.7 and m_position.y() < height*0.06:
            self.m_flag = True
            if Qt.LeftButton and self.m_flag:                
                pos_x = int(self.m_Position.x())
                pos_y = int(self.m_Position.y())
                if pos_x < width*0.7 and pos_y < height*0.06:           
                    self.move(QMouseEvent.globalPos() - self.m_Position)  # 更改窗口位置
                    QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        self.m_flag = False
        self.setCursor(QCursor(Qt.ArrowCursor))
    
    def closeEvent(self, event):
        
        self.device_a.StopImmediate()
        self.device_a.StopPolling()
        self.device_a.Disconnect(True)

if __name__ == '__main__':

    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    app.exec()
