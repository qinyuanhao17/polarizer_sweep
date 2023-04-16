import clr 
import os 
import time 
import sys

# Write in file paths of dlls needed. 
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.IntegratedStepperMotorsCLI.dll")

# Import functions from dlls. 
from Thorlabs.MotionControl import DeviceManagerCLI
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.IntegratedStepperMotorsCLI import *
from Thorlabs.MotionControl.IntegratedStepperMotorsCLI import CageRotator
from System import Decimal 

# Build device list.  
DeviceManagerCLI.BuildDeviceList()

# create new device.
# serial_no = "55001052"
serial_no = "55342484"  # Replace this line with your device's serial number.
device = CageRotator.CreateCageRotator(serial_no)

# Connect to device. 
device.Connect(serial_no)
rtn = device.IsConnected
print(rtn)
# Ensure that the device settings have been initialized.
if not device.IsSettingsInitialized():
    device.WaitForSettingsInitialized(3000)  # 10 second timeout.
    assert device.IsSettingsInitialized() is True

# Start polling loop and enable device.
device.StartPolling(250)  #250ms polling rate.

device.EnableDevice()
time.sleep(0.25)  # Wait for device to enable.

# Get Device Information and display description.
device_info = device.GetDeviceInfo()
print(device_info.Description)
# Load any configuration settings needed by the controller/stage.
device.LoadMotorConfiguration(serial_no, DeviceConfiguration.DeviceSettingsUseOptionType.UseDeviceSettings)
motor_config = device.LoadMotorConfiguration(serial_no)
device.Home(60000)  # 60 second timeout.
# time.sleep(5)
# new_pos = Decimal(30.0)  # Must be a .NET decimal.
# print(type(new_pos))
# print(f'Moving to {new_pos}')
# workDone = device.InitializeWaitHandler()

# device.MoveTo(new_pos,workDone)  # 60 second timeout.
print("Done")