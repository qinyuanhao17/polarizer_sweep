import sys
import time
import clr
import nidaqmx
import pythoncom
import re
import serial
import polarizer_sweep_ui
import serial.tools.list_ports as lp
from threading import Thread
from PyQt5.QtGui import QIcon, QPixmap, QCursor, QMouseEvent, QColor, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QEvent
from PyQt5.QtWidgets import QWidget, QApplication, QGraphicsDropShadowEffect,QDesktopWidget, QFileDialog, QVBoxLayout, QMessageBox

# Write in file paths of dlls needed. 
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.IntegratedStepperMotorsCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.KCube.InertialMotorCLI.dll")

# Import functions from dlls. 
from Thorlabs.MotionControl import DeviceManagerCLI
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import MotorDirection
from Thorlabs.MotionControl.IntegratedStepperMotorsCLI import *
from Thorlabs.MotionControl.IntegratedStepperMotorsCLI import CageRotator
from Thorlabs.MotionControl.KCube.InertialMotorCLI import *
from Thorlabs.MotionControl.KCube.InertialMotorCLI import KCubeInertialMotor
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
        self.ui_width = int(QDesktopWidget().availableGeometry().size().width()*0.48)
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
        # self.connect_thread()
        # self.rotator_a_velocity_acceleration_step_set()
        # init rotator B signal
        self.rotator_b_signal()
        # # init rotator B info ui
        self.rotator_b_info_ui()

        # # connect and set when boot
        # self.b_connect_thread()
        # # self.rotator_a_velocity_acceleration_step_set()
        
        '''ANC300 Init'''
        # Turn on ANC 300
        self.anc_comport_read()
        # anc signal init
        self.anc_signal()

        '''Pump K-Cube Signal'''
        self.pump_signal()
    '''Pump K-Cube Control'''
    def pump_signal(self):
        self.pump_connect_btn.clicked.connect(self.pump_connect_thread)
        self.pump_ch1_set_btn.clicked.connect(self.pump_ch1_set)
        self.pump_ch2_set_btn.clicked.connect(self.pump_ch2_set)
        self.pump_ch1_move_tbtn.clicked.connect(self.pump_ch1_move_thread)
        self.pump_ch2_move_tbtn.clicked.connect(self.pump_ch2_move_thread)
        self.pump_ch1_ledit.returnPressed.connect(self.pump_ch1_move_thread)
        self.pump_ch2_ledit.returnPressed.connect(self.pump_ch2_move_thread)
        self.pump_ch1_forward_btn.clicked.connect(self.pump_ch1_step_forward_tread)
        self.pump_ch2_forward_btn.clicked.connect(self.pump_ch2_step_forward_tread)
        self.pump_ch1_backward_btn.clicked.connect(self.pump_ch1_step_backward_tread)
        self.pump_ch2_backward_btn.clicked.connect(self.pump_ch2_step_backward_tread)
        self.pump_ch1_stop_tbtn.clicked.connect(self.pump_ch1_stop)
        self.pump_ch2_stop_tbtn.clicked.connect(self.pump_ch2_stop)
        self.pump_disconnect_btn.clicked.connect(self.pump_disconnect)
    def pump_disconnect(self):
        self.device_pump.StopPolling()
        self.device_pump.Disconnect()
    def pump_ch1_stop(self):
        self.device_pump.Stop(self.chan1)
    def pump_ch2_stop(self):
        self.device_pump.Stop(self.chan2)
    def pump_ch1_step_forward_tread(self):
        thread = Thread(
            target=self.pump_ch1_step_forward
        )
        thread.start()
    def pump_ch2_step_forward_tread(self):
        thread = Thread(
            target=self.pump_ch2_step_forward
        )
        thread.start()
    def pump_ch1_step_forward(self):
        pythoncom.CoInitialize()
        if self.device_pump.IsAnyChannelMoving():
            pass
        else:
            step = int(self.pump_ch1_step_move_spbx.text())
            current_position = self.device_pump.GetPosition(self.chan1)
            new_pos = step + current_position
            self.device_pump.MoveTo(self.chan1, new_pos, 60000) 
        pythoncom.CoUninitialize()
    def pump_ch2_step_forward(self):
        pythoncom.CoInitialize()
        if self.device_pump.IsAnyChannelMoving():
            pass
        else:
            step = int(self.pump_ch2_step_move_spbx.text())
            current_position = self.device_pump.GetPosition(self.chan2)
            new_pos = step + current_position
            self.device_pump.MoveTo(self.chan2, new_pos, 60000) 
        pythoncom.CoUninitialize()
    def pump_ch1_step_backward_tread(self):
        thread = Thread(
            target=self.pump_ch1_step_backward
        )
        thread.start()
    def pump_ch2_step_backward_tread(self):
        thread = Thread(
            target=self.pump_ch2_step_backward
        )
        thread.start()
    def pump_ch1_step_backward(self):
        pythoncom.CoInitialize()
        if self.device_pump.IsAnyChannelMoving():
            pass
        else:
            step = int(self.pump_ch1_step_move_spbx.text())
            current_position = self.device_pump.GetPosition(self.chan1)
            new_pos = current_position - step
            self.device_pump.MoveTo(self.chan1, new_pos, 60000) 
        pythoncom.CoUninitialize()
    def pump_ch2_step_backward(self):
        pythoncom.CoInitialize()
        if self.device_pump.IsAnyChannelMoving():
            pass
        else:
            step = int(self.pump_ch2_step_move_spbx.text())
            current_position = self.device_pump.GetPosition(self.chan2)
            new_pos = current_position - step
            self.device_pump.MoveTo(self.chan2, new_pos, 60000) 
        pythoncom.CoUninitialize()
    def pump_ch1_move_thread(self):
        thread = Thread(
            target=self.pump_ch1_move
        )
        thread.start()
    def pump_ch2_move_thread(self):
        thread = Thread(
            target=self.pump_ch2_move
        )
        thread.start()
    def pump_ch1_move(self):
        pythoncom.CoInitialize()
        if self.device_pump.IsAnyChannelMoving():
            pass
        else:
            if self.is_number(self.pump_ch1_ledit.text()):
                if int(self.pump_ch1_ledit.text()) != self.device_pump.GetPosition(self.chan1):
                    new_pos = int(self.pump_ch1_ledit.text())
                    self.device_pump.MoveTo(self.chan1, new_pos, 60000) 
                    self.pump_ch1_ledit.clear()
        pythoncom.CoUninitialize()
    def pump_ch2_move(self):
        pythoncom.CoInitialize()
        if self.device_pump.IsAnyChannelMoving():
            pass
        else:
            if self.is_number(self.pump_ch2_ledit.text()):
                if int(self.pump_ch2_ledit.text()) != self.device_pump.GetPosition(self.chan2):
                    new_pos = int(self.pump_ch2_ledit.text())
                    self.device_pump.MoveTo(self.chan2, new_pos, 60000) 
                    self.pump_ch2_ledit.clear()
        pythoncom.CoUninitialize()            
    def pump_ch1_set(self):
        step_rate = int(self.pump_ch1_step_spbx.text())
        step_acc = int(self.pump_ch1_step_spbx.text())
        self.device_settings.Drive.Channel(self.chan1).StepRate = step_rate
        self.device_settings.Drive.Channel(self.chan1).StepAcceleration = step_acc
        # Send settings to the device
        self.device_pump.SetSettings(self.device_settings, True, True)
    def pump_ch2_set(self):
        step_rate = int(self.pump_ch2_step_spbx.text())
        step_acc = int(self.pump_ch2_step_spbx.text())
        self.device_settings.Drive.Channel(self.chan2).StepRate = step_rate
        self.device_settings.Drive.Channel(self.chan2).StepAcceleration = step_acc
        # Send settings to the device
        self.device_pump.SetSettings(self.device_settings, True, True)
    def pump_connect_thread(self):
        pump_connect_thread = Thread(
            target=self.pump_connect
        )
        pump_connect_thread.start()
    def pump_connect(self):
        pythoncom.CoInitialize()
        
        serial_number = self.pump_serial_cbox.currentText().strip('S/N ')
        # Init rotator A self.device_a
        DeviceManagerCLI.BuildDeviceList()
        self.device_pump = KCubeInertialMotor.CreateKCubeInertialMotor(serial_number)
        self.device_pump.Connect(serial_number)

        # Start polling loop and enable self.device_a.
        polling_rate = 250
        self.device_pump.StartPolling(polling_rate)  #250ms polling rate.

        self.device_pump.EnableDevice()
        time.sleep(0.25)  # Wait for self.device_a to enable.
        device_info = self.device_pump.GetDeviceInfo()
        print(device_info.Description)
        # Load any configuration settings needed by the controller/stage.
        inertial_motor_config = self.device_pump.GetInertialMotorConfiguration(serial_number)
        self.device_settings = ThorlabsInertialMotorSettings.GetSettings(inertial_motor_config)
        # Step parameters for an intertial motor channel
        self.chan1 = InertialMotorStatus.MotorChannels.Channel1  # enum chan ident
        self.chan2 = InertialMotorStatus.MotorChannels.Channel2  # enum chan ident

        pythoncom.CoUninitialize()
        pump_position_view_thread = Thread(
            target=self.pump_position_view_func
        )
        pump_position_view_thread.start()

    def pump_position_view_func(self):
        pythoncom.CoInitialize()
        while True:
            if self.device_pump.IsConnected:
                
                self.pump_ch1_position_view.display(int(self.device_pump.GetPosition(self.chan1)))
                self.pump_ch2_position_view.display(int(self.device_pump.GetPosition(self.chan2)))
                time.sleep(0.2)
            else:
                break
        pythoncom.CoUninitialize()
    '''ANC300 Control'''
    def anc_signal(self):
        # axis 1 signal
        self.ax1_on_btn.clicked.connect(self.ax1_on)
        self.ax1_off_btn.clicked.connect(self.ax1_off)
        self.anc300_connect_btn.clicked.connect(self.anc_connect)
        self.ax1_cap_meas_btn.clicked.connect(self.ax1_capacity_measure)
        self.ax1_set_btn.clicked.connect(self.ax1_freq_vol_set)

        self.x_plus_btn.clicked.connect(self.ax1_stp_plus)
        self.x_minus_btn.clicked.connect(self.ax1_stp_minus)
        self.x_plus_btn.pressed.connect(self.ax1_continue_plus)
        self.x_minus_btn.pressed.connect(self.ax1_continue_minus)
        self.x_plus_btn.released.connect(self.ax1_stop)
        self.x_minus_btn.released.connect(self.ax1_stop)

        # axis 2 signal
        self.ax2_on_btn.clicked.connect(self.ax2_on)
        self.ax2_off_btn.clicked.connect(self.ax2_off)
        self.ax2_cap_meas_btn.clicked.connect(self.ax2_capacity_measure)
        self.ax2_set_btn.clicked.connect(self.ax2_freq_vol_set)

        self.y_plus_btn.clicked.connect(self.ax2_stp_plus)
        self.y_minus_btn.clicked.connect(self.ax2_stp_minus)
        self.y_plus_btn.pressed.connect(self.ax2_continue_plus)
        self.y_minus_btn.pressed.connect(self.ax2_continue_minus)
        self.y_plus_btn.released.connect(self.ax2_stop)
        self.y_minus_btn.released.connect(self.ax2_stop)
    def anc_comport_read(self):
        rs = list(lp.comports())
        for item in rs:
            item = str(item)
            index = item.index('-')
            item = item[0:index-1]
            self.anc_cbx.addItem(item)
    def anc_connect(self):
        comport = self.anc_cbx.currentText()
        
        self.anc300 = serial.Serial(comport,115200,timeout=1)
    def ax1_on(self):
        self.anc300.write(b'setm 1 stp \r\n')
    def ax1_off(self):
        self.anc300.write(b'setm 1 gnd \r\n')
    def ax1_capacity_measure(self):
        self.anc300.write(b'getc 1 \r\n')
        while True:
            response = self.anc300.readlines()
            if response:
                for line in response:
                    line = str(line.rstrip(),'utf-8')              
                    if line[0:11] == 'capacitance':
                        
                        line = str(line)
                        index = line.index('=')
                        self.ax1_cap_ledit.setText(line[index+2:index+7])
                    
            else:
                break
        self.anc300.write(b'capw 1 \r\n')
    def ax1_freq_vol_set(self):
        freq = int(self.ax1_freq_spbx.text())
        vol = int(self.ax1_vol_spbx.text())
        freq_signal = 'setf 1 {} \r\n'.format(freq)
        vol_signal = 'setv 1 {} \r\n'.format(vol)
        rtn = self.anc300.write(freq_signal.encode())
        rtn = self.anc300.write(vol_signal.encode())
    def ax1_stp_plus(self):
        rtn = self.anc300.write(b'stepu 1 1 \r\n')
        rtn = self.anc300.write(b'stepw 1 \r\n')
    def ax1_stp_minus(self):
        rtn = self.anc300.write(b'stepd 1 1 \r\n')
        rtn = self.anc300.write(b'stepw 1 \r\n')
    def ax1_continue_plus(self):
        rtn = self.anc300.write(b'stepu 1 C \r\n')
        # rtn = self.anc300.write(b'stepw 1 \r\n')
    def ax1_continue_minus(self):
        rtn = self.anc300.write(b'stepd 1 C \r\n')
        # rtn = self.anc300.write(b'stepw 1 \r\n')
    def ax1_stop(self):
        rtn = self.anc300.write(b'stop 1 \r\n')

    def ax2_on(self):
        self.anc300.write(b'setm 2 stp \r\n')
    def ax2_off(self):
        self.anc300.write(b'setm 2 gnd \r\n')
    def ax2_capacity_measure(self):
        self.anc300.write(b'getc 2 \r\n')
        while True:
            response = self.anc300.readlines()
            if response:
                for line in response:
                    line = str(line.rstrip(),'utf-8')              
                    if line[0:22] == 'capacitance':
                        
                        line = str(line)
                        index = line.index('=')
                        self.ax2_cap_ledit.setText(line[index+2:index+7])
                    
            else:
                break
        self.anc300.write(b'capw 2 \r\n')
    def ax2_freq_vol_set(self):
        freq = int(self.ax2_freq_spbx.text())
        vol = int(self.ax2_vol_spbx.text())
        freq_signal = 'setf 2 {} \r\n'.format(freq)
        vol_signal = 'setv 2 {} \r\n'.format(vol)
        rtn = self.anc300.write(freq_signal.encode())
        rtn = self.anc300.write(vol_signal.encode())
    def ax2_stp_plus(self):
        rtn = self.anc300.write(b'stepd 2 1 \r\n')
        rtn = self.anc300.write(b'stepw 2 \r\n')
    def ax2_stp_minus(self):
        rtn = self.anc300.write(b'stepu 2 1 \r\n')
        rtn = self.anc300.write(b'stepw 2 \r\n')
    def ax2_continue_plus(self):
        rtn = self.anc300.write(b'stepd 2 C \r\n')
        # rtn = self.anc300.write(b'stepw 2 \r\n')
    def ax2_continue_minus(self):
        rtn = self.anc300.write(b'stepu 2 C \r\n')
        # rtn = self.anc300.write(b'stepw 2 \r\n')
    def ax2_stop(self):
        rtn = self.anc300.write(b'stop 2 \r\n')
    '''Set Rotator A'''
    def rotator_a_signal(self):
        self.rotator_a_connect_btn.clicked.connect(self.connect_thread)

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
        pythoncom.CoInitialize()
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
        pythoncom.CoUninitialize()
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
       
        pythoncom.CoInitialize()
        if self.device_a.IsConnected:
            workDone = self.device_a.InitializeWaitHandler()
            self.device_a.SetHomingVelocity(Decimal(10))
            self.device_a.Home(workDone)
            
            if self.device_a.Status.IsHomed:
                self.rotator_a_info.emit('Rotator A is homed.')
                self.rotator_a_info.emit('-'*60)
                
        else:
            self.rotator_a_info.emit('Device is not connected.')
            self.rotator_a_info.emit('-'*60)
        pythoncom.CoUninitialize()
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
        if self.is_number(self.rot_a_ledit.text()):
            velPars = self.device_a.GetVelocityParams()
            velPars.MaxVelocity = Decimal(15)
            self.device_a.SetVelocityParams(velPars)

            new_position = Decimal(float(self.rot_a_ledit.text()))
            workDone = self.device_a.InitializeWaitHandler()
            self.device_a.MoveTo(new_position, workDone)
            self.rot_a_ledit.clear()
        else:
            self.rot_a_ledit.clear()
            pass
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
        thread_read_write = Thread(
            target= self.rotator_a_read_write_thread
        )
        thread_read_write.start()
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
        pythoncom.CoInitialize()
        
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
        
        pythoncom.CoUninitialize()                   
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

    def rotator_b_signal(self):
        self.rotator_b_connect_btn.clicked.connect(self.b_connect_thread)
        # Home button signal
        self.b_home_tbtn.clicked.connect(self.rotator_b_home)
        # Disconnect button signal
        self.b_disconnect_btn.clicked.connect(self.rotator_b_disconnect)
        #message signal
        self.rotator_b_info.connect(self.rotator_b_slot)
        self.rotator_b_progress_bar_info.connect(self.rotator_b_progress_bar_thread)
        # scroll area scrollbar signal
        self.rot_b_scroll.verticalScrollBar().rangeChanged.connect(
            lambda: self.rot_b_scroll.verticalScrollBar().setValue(
                self.rot_b_scroll.verticalScrollBar().maximum()
            )
        )
        # move to signal
        self.b_move_tbtn.clicked.connect(self.rotator_b_move_to_position)
        self.rot_b_ledit.returnPressed.connect(self.rotator_b_move_to_position)
        # stop signal
        self.b_stop_tbtn.clicked.connect(self.rotator_b_stop)
        # drive signal
        self.rotator_b_set_btn.clicked.connect(self.rotator_b_velocity_acceleration_step_set)
        self.rotator_b_forward_btn.clicked.connect(self.rotator_b_step_forward)
        self.rotator_b_backward_btn.clicked.connect(self.rotator_b_step_backward)
        self.rotator_b_forward_btn.pressed.connect(self.rotator_b_continuous_forward_pressed)
        self.rotator_b_backward_btn.pressed.connect(self.rotator_b_continuous_backward_pressed)
        self.rotator_b_forward_btn.released.connect(self.rotator_b_continuous_released)
        self.rotator_b_backward_btn.released.connect(self.rotator_b_continuous_released)
        # Polarization sweep signal
        self.rotator_b_sweep_start_btn.clicked.connect(self.power_sweep)
        self.rotator_b_interrupt_btn.clicked.connect(self.rotator_b_stop_sweep)
        # fram calculation signal
        self.rotator_b_calc_btn.clicked.connect(self.rotator_b_frame_calc)
    def b_connect_thread(self):
        boot_thread = Thread(
            target=self.rotator_b_connect
        )
        boot_thread.start()
    
    def rotator_b_connect(self):
        pythoncom.CoInitialize()
        serial_number = self.rotator_b_serial_cbox.currentText().strip('S/N ')
        # Init rotator A self.device_a
        DeviceManagerCLI.BuildDeviceList()
        self.device_b = CageRotator.CreateCageRotator(serial_number)
        self.device_b.Connect(serial_number)
        rtn = self.device_b.IsConnected
        if rtn:
             self.rotator_b_info.emit('Rotator B is connected')
        # Ensure that the self.device_b settings have been initialized.
        if not self.device_b.IsSettingsInitialized():
            self.device_b.WaitForSettingsInitialized(3000)  # 3 second timeout.
            assert self.device_b.IsSettingsInitialized() is True

        # Start polling loop and enable self.device_a.
        polling_rate = 250
        self.device_b.StartPolling(polling_rate)  #250ms polling rate.
        self.rotator_b_info.emit('Polling rate: {}'.format(polling_rate))
        self.device_b.EnableDevice()
        time.sleep(0.25)  # Wait for self.device_a to enable.

        # Get Device Information and display description.
        device_info = self.device_b.GetDeviceInfo()
        self.rotator_b_info.emit('{}: {}'.format(device_info.Description,self.rotator_b_serial_cbox.currentText()))
        self.rotator_b_info.emit('-'*60)
        # Load any configuration settings needed by the controller/stage.
        self.device_b.LoadMotorConfiguration(serial_number, DeviceConfiguration.DeviceSettingsUseOptionType.UseDeviceSettings)
        self.device_b.LoadMotorConfiguration(serial_number)

        pythoncom.CoUninitialize()
        thread = Thread(
            target=self.rotator_b_position_view
        )
        thread.start()
    
    def rotator_b_position_view(self):
        pythoncom.CoInitialize()
        self.b_position_view.setSmallDecimalPoint(True)
        while True:
            if self.device_b.IsConnected:

                self.b_position_view.display(float(str(self.device_b.Position)))
                time.sleep(0.2)
            else:
                break
        pythoncom.CoUninitialize()
    def rotator_b_home(self):
        if self.device_b.Status.IsHoming:
            pass
        else:
            self.rotator_b_info.emit('Rotator B is homimg, please wait.')
            thread = Thread(
                target = self.rotator_b_home_thread
            )
            thread.start()
    def rotator_b_home_thread(self):
        
        pythoncom.CoInitialize()
        if self.device_b.IsConnected:
            self.device_b.SetHomingVelocity(Decimal(10))
            self.device_b.Home(60000)
            
            if self.device_b.Status.IsHomed:
                self.rotator_b_info.emit('Rotator B is homed.')
                self.rotator_b_info.emit('-'*60)
                
        else:
            self.rotator_b_info.emit('Device is not connected.')
            self.rotator_b_info.emit('-'*60)
        pythoncom.CoUninitialize()

    def rotator_b_disconnect(self):
        self.device_b.StopPolling()
        self.device_b.Disconnect(True)
        if not self.device_b.IsConnected:
            self.rotator_b_info.emit('Rotator B is disconnected.')
            self.rotator_b_info.emit('-'*60)
    
    '''Set Rotator B info ui'''
    def rotator_b_info_ui(self):

        self.rot_b_msg.setWordWrap(True)  # 自动换行
        self.rot_b_msg.setAlignment(Qt.AlignTop)  # 靠上

        # 用于存放消息
        self.rot_b_msg_history = []

    def rotator_b_slot(self, msg):

        self.rot_b_msg_history.append(msg)
        self.rot_b_msg.setText("<br>".join(self.rot_b_msg_history))
        self.rot_b_msg.resize(400, self.rot_b_msg.frameSize().height() + 20)
        self.rot_b_msg.repaint()  # 更新内容，如果不更新可能没有显示新内容   
    def rotator_b_move_to_position(self):
        if self.is_number(self.rot_b_ledit.text()):
            velPars = self.device_b.GetVelocityParams()
            velPars.MaxVelocity = Decimal(15)
            self.device_b.SetVelocityParams(velPars)

            new_position = Decimal(float(self.rot_b_ledit.text()))
            workDone = self.device_b.InitializeWaitHandler()
            self.device_b.MoveTo(new_position, workDone)
            self.rot_b_ledit.clear()
        else:
            self.rot_b_ledit.clear()
            pass
    def rotator_b_stop(self):
        self.device_b.StopImmediate()
    def rotator_b_step_forward(self):
        if self.device_b.Status.IsInMotion:
            pass
        else:
            if self.rotator_b_stp_rdbtn.isChecked():
                step = Decimal(float(self.rotator_b_step_spbx.text()))
                current_position = self.device_b.Position
                new_position = current_position + step
                workDone = self.device_b.InitializeWaitHandler()
                self.device_b.MoveTo(new_position, workDone)
                
            elif self.rotator_b_cont_rdbtn.isChecked():
                pass
    def rotator_b_step_backward(self):
        if self.device_b.Status.IsInMotion:
            pass
        else:
            if self.rotator_b_stp_rdbtn.isChecked():
                step = Decimal(float(self.rotator_b_step_spbx.text()))
                current_position = self.device_b.Position
                new_position = current_position - step
                workDone = self.device_b.InitializeWaitHandler()
                if float(str(new_position)) >= 0:
                    self.device_b.MoveTo(new_position, workDone)
                elif float(str(new_position)) < 0:
                    new_position = Decimal(new_position+360)
                    self.device_b.MoveTo(new_position, workDone)
                
            elif self.rotator_b_cont_rdbtn.isChecked():
                pass
    def rotator_b_continuous_forward_pressed(self):
        if self.rotator_b_stp_rdbtn.isChecked():
            pass
        elif self.rotator_b_cont_rdbtn.isChecked():
            new_direction_forward = MotorDirection.Forward 
            self.device_b.MoveContinuous(MotorDirection.Forward)
    def rotator_b_continuous_backward_pressed(self):
        if self.rotator_b_stp_rdbtn.isChecked():
            pass
        elif self.rotator_b_cont_rdbtn.isChecked():
            new_direction_forward = MotorDirection.Backward 
            self.device_b.MoveContinuous(MotorDirection.Backward)
    def rotator_b_velocity_acceleration_step_set(self):
        
        new_velocity = Decimal(int(self.rotator_b_velocity_spbx.text()))
        new_acceleration = Decimal(int(self.rotator_b_acceleration_spbx.text()))
        new_step = Decimal(float(self.rotator_b_step_spbx.text()))
        velPars = self.device_b.GetVelocityParams()
        velPars.MaxVelocity = new_velocity
        velPars.Acceleration = new_acceleration
        
        self.device_b.SetVelocityParams(velPars)
        
        self.device_b.SetVelocityParams(velPars)


        self.rotator_b_info.emit('Velocity: {}'.format(new_velocity))
        self.rotator_b_info.emit('Acceleration: {}'.format(new_acceleration))
        self.rotator_b_info.emit('Step: {}'.format(new_step))
        self.rotator_b_info.emit('-'*60)
    def rotator_b_continuous_released(self):
        self.device_b.StopImmediate() 

    ''' Power Sweep'''
    def power_sweep(self):
        thread_read_write = Thread(
            target= self.rotator_b_read_write_thread
        )
        thread_read_write.start()
    def rotator_b_progress_bar_thread(self,msg):
        self.rotator_b_progressbar.setValue(int(msg))
    def rotator_b_frame_calc(self):
        b_start_position = float(self.rotator_b_startpos_spbx.text())
        b_stop_position = float(self.rotator_b_stoppos_spbx.text())
        b_step = float(self.rotator_b_sweepstep_spbx.text())
        
        tot_frame = int((b_stop_position - b_start_position)/b_step+1)
        new_position = Decimal(b_start_position)
        workDone = self.device_b.InitializeWaitHandler()
        self.device_b.MoveTo(new_position, workDone)
        time.sleep(0.5)
        if self.device_b.IsConnected:
            self.rotator_b_frame_spbx.setValue(tot_frame)    
            
    def rotator_b_read_write_thread(self):
        pythoncom.CoInitialize()
        b_start_position = float(self.rotator_b_startpos_spbx.text())
        b_stop_position = float(self.rotator_b_stoppos_spbx.text())
        b_step = float(self.rotator_b_sweepstep_spbx.text())
        b_stime = float(self.rotator_b_stime_spbx.text())
        tot_frame = int((b_stop_position - b_start_position)/b_step+1)

        with nidaqmx.Task() as read_task, nidaqmx.Task() as write_task:
    
            di = read_task.di_channels.add_di_chan("Dev1/port0/line1")
            do = write_task.do_channels.add_do_chan("Dev1/port0/line0")           
            
            i = 0
            self.__stopConstantB = False
            while i < (tot_frame+1):
                
                if self.__stopConstantB == False:
                    self.rotator_b_progress_bar_info.emit(i/tot_frame*100)
                    if self.device_b.IsConnected:
                        data = read_task.read()
                        if  data == False:    
                            write_task.write(True)
                            time.sleep(0.25)
                            write_task.write(False)
                            time.sleep(b_stime+2)             
                            self.rotator_b_info.emit('{}'.format(i))
                            if i == tot_frame:
                                pass 
                            else:
                                current_position = self.device_b.Position
                                new_position = current_position + Decimal(b_step)
                                workDone = self.device_b.InitializeWaitHandler()
                                self.device_b.MoveTo(new_position, workDone)
                                time.sleep(0.5)
                                while True:
                                    if self.device_b.Status.IsInMotion:
                                        time.sleep(0.01)
                                    else:
                                        break                          
                            i += 1
                            
                    else:
                        break            
                else:
                    break 
        pythoncom.CoUninitialize()

    def rotator_b_stop_sweep(self):
        self.__stopConstantB = True 
    
    def is_number(self,string):
        pattern = r'^[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?$'
        return bool(re.match(pattern, string))
    

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
        self.device_b.StopImmediate()
        self.device_b.StopPolling()
        self.device_b.Disconnect(True)
        self.anc300.close()

if __name__ == '__main__':

    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    app.exec()
