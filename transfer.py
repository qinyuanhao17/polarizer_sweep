    '''Set Rotator B'''
    def rotator_b_signal(self):
        self.rotator_b_connect_btn.clicked.connect(self.b_rotator_connect)

        #message signal
        self.rotator_b_info.connect(self.rotator_b_slot)
        self.rotator_b_progress_bar_info.connect(self.rotator_b_progress_bar_thread)
        # scroll area scrollbar signal
        self.rot_b_scroll.verticalScrollBar().rangeChanged.connect(
            lambda: self.rot_b_scroll.verticalScrollBar().setValue(
                self.rot_b_scroll.verticalScrollBar().maximum()
            )
        )
        # Home button signal
        self.b_home_tbtn.clicked.connect(self.rotator_b_home)
        # Disconnect button signal
        self.b_disconnect_btn.clicked.connect(self.rotator_b_disconnect)
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
    def rotator_b_stop_sweep(self):
        self.__stopConstantB = True
    def b_connect_thread(self):
        boot_thread = Thread(
            target=self.b_rotator_connect
        )
        boot_thread.start()

    def b_rotator_connect(self):
        serial_number = self.rotator_b_serial_cbox.currentText().strip('S/N ')
        # Init rotator B self.device_b
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

        # Start polling loop and enable self.device_b.
        polling_rate = 250
        self.device_b.StartPolling(polling_rate)  #250ms polling rate.
        self.rotator_b_info.emit('Polling rate: {}'.format(polling_rate))
        self.device_b.EnableDevice()
        time.sleep(0.25)  # Wait for self.device_b to enable.

        # Get Device Information and display description.
        device_info = self.device_b.GetDeviceInfo()
        self.rotator_b_info.emit('{}: {}'.format(device_info.Description,self.rotator_b_serial_cbox.currentText()))
        self.rotator_b_info.emit('-'*60)
        # Load any configuration settings needed by the controller/stage.
        self.device_b.LoadMotorConfiguration(serial_number, DeviceConfiguration.DeviceSettingsUseOptionType.UseDeviceSettings)
        self.device_b.LoadMotorConfiguration(serial_number)
        thread = Thread(
            target=self.rotator_b_position_view
        )
        thread.start()
        
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
        if self.device_b.IsConnected:
            self.device_b.Home(60000)
            
            if self.device_b.Status.IsHomed:
                self.rotator_b_info.emit('Rotator B is homed.')
                self.rotator_b_info.emit('-'*60)
                
        else:
            self.rotator_b_info.emit('Device is not connected.')
            self.rotator_b_info.emit('-'*60)
            
    def rotator_b_disconnect(self):
        self.device_b.StopPolling()
        self.device_b.Disconnect(True)
        if not self.device_b.IsConnected:
            self.rotator_b_info.emit('Rotator B is disconnected.')
            self.rotator_b_info.emit('-'*60)
    def rotator_b_position_view(self):
        
        self.b_position_view.setSmallDecimalPoint(True)
        while True:
            if self.device_b.IsConnected:

                self.b_position_view.display(float(str(self.device_b.Position)))
                time.sleep(0.2)
            else:
                break
    def rotator_b_move_to_position(self):
        
        velPars = self.device_b.GetVelocityParams()
        velPars.MaxVelocity = Decimal(15)
        self.device_b.SetVelocityParams(velPars)

        new_position = Decimal(float(self.rot_b_ledit.text()))
        workDone = self.device_b.InitializeWaitHandler()
        self.device_b.MoveTo(new_position, workDone)
        self.rot_b_ledit.clear()
    def rotator_b_stop(self):
        self.device_b.StopImmediate()
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
    
    def rotator_b_continuous_released(self):
        self.device_b.StopImmediate()

    ''' Polarization Sweep'''
    def power_sweep(self):
        self.thread_read_write = Thread(
            target= self.rotator_b_read_write_thread
        )
        self.thread_read_write.start()
    def rotator_b_progress_bar_thread(self,msg):
        self.rotato_b_progressbar.setValue(int(msg))
    def rotator_b_frame_calc(self):
        b_start_position = float(self.rotator_b_startpos_spbx.text())
        b_stop_position = float(self.rotator_b_stoppos_spbx.text())
        b_step = float(self.rotator_b_sweepstep_spbx.text())
        b_stime = float(self.rotator_b_stime_spbx.text())
        tot_frame = int((b_stop_position - b_start_position)/b_step+1)
        new_position = Decimal(b_start_position)
        workDone = self.device_b.InitializeWaitHandler()
        self.device_b.MoveTo(new_position, workDone)
        time.sleep(0.5)
        if self.device_b.IsConnected:
            self.rotator_b_frame_spbx.setValue(tot_frame)    
            
    def rotator_b_read_write_thread(self):
        
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
                            time.sleep(0.01)
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