
from app_error import NoMonitor, SysStatusError, NoMonitorNameError, NoWiFiError, NoDBidError, NoConfigFile, blink
from wifi_connect import WifiAccess
from send_reading import SendReading
from config import exists_config
from atm90e32_u import ATM90e32
import time
import machine
# ***** Set up debug LEDs
# A red one for errors
# A green one for ok.
led_red = machine.Pin(27, machine.Pin.OUT)
led_green = machine.Pin(32, machine.Pin.OUT)
# I'm not delaying readings because there is a pause in the atm90e32
# TIME_BETWEEN_READINGS = 1


# ***** atm90e32 CALIBRATION SETTINGS *****/
# Based on the CT and power transformer being used.
# See http://bit.ly/2ED1MSD
lineFreq = 4485  # 4485 for 60 Hz (North America)
# 389 for 50 hz (rest of the world)
PGAGain = 21     # 21 for 100A (2x), 42 for >100A (4x)

# VoltageGain = 42080  # 42080 - 9v AC transformer.
# 32428 - 12v AC Transformer
VoltageGain = 36650  # What I calculated based on reading app notes on calibration
CurrentGainCT1 = 25368  # My calculation
CurrentGainCT2 = 25368  # My calculation
# CurrentGainCT1 = 25498  # 38695 - SCT-016 120A/40mA
# CurrentGainCT2 = 25498  # 25498 - SCT-013-000 100A/50mA
# 46539 - Magnalab 100A w/ built in burden resistor
# ****** Input Variables ******/
# The one input variable we need to know is the name of the config file to use.
# The config file identifies the monitor and contains connection info to the
#  Rasp Pi
# config_filenamne = input('enter the config filename: ')
# config_filename = "config_aggregate.json"
print("in test")
try:
    exists_config()
except OSError as err:
    blink(led_red, NoConfigFile().blinks)
else:
    # *******************************************/
    # Get the wifi up and running...
    # First blink the green LED so we know we're in main.py
    blink(led_green, 2)
    # Load up an instance of wifi.
    join_wifi = WifiAccess()
    if (not join_wifi.get_connected()):
        # Keep blinking...we cabn't do anything.
        blink(led_red, SysStatusError().blinks)

    # *******************************************/
    # Delay starting up to accomodate plugging in energy monitor after microcontroller.
    # TBD: Some kind of "bug" that I have to make sure to plug the energy monitor in
    # AFTER the esp32. It shouldn't matter...there's something going on with the SPI
    # traffic.
    time.sleep(2)

    energy_sensor = ATM90e32(lineFreq, PGAGain,
                             VoltageGain, CurrentGainCT1, 0, CurrentGainCT2)
    time.sleep(.5)
    # Maybe we don't have to initialize a second time...I found working with a
    # different atm90 that initializing twice was more robust than once.
    energy_sensor = ATM90e32(lineFreq, PGAGain,
                             VoltageGain, CurrentGainCT1, 0, CurrentGainCT2)

    # We have an instance of the atm90e32.  Let's check if we get senible readings
    sys0 = energy_sensor.sys_status0
    if (sys0 == 0xFFFF or sys0 == 0):
        raise OSError(SysStatusError().number,
                      SysStatusError().explanation)
    s = SendReading()
    print('monitor name: {}.....project ID: {}'.format(
        s.monitor_name, s.project_id))
    # Check that monitor is working
    sys0 = energy_sensor.sys_status0
    if (sys0 == 0xFFFF or sys0 == 0):
        raise OSError(SysStatusError().number,
                      SysStatusError().explanation)
    Pa = energy_sensor.total_active_power
    Pr = energy_sensor.total_reactive_power
    print('aggregate active power: {}...aggregate reactive power: {}'.format(Pa, Pr))
    s.send(Pa, Pr)
