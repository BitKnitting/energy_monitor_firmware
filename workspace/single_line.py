
#######################################################################
# I used this code when I wanted a "quick and dirty" way to read the
# power being used by our heater.
#######################################################################
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
TIME_BETWEEN_READINGS = 2

led_red = machine.Pin(27, machine.Pin.OUT)
led_green = machine.Pin(32, machine.Pin.OUT)
# ***** atm90e32 CALIBRATION SETTINGS *****/
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
    time.sleep(3)

    try:
        # Get reading and then send reading.
        # Initializing the atm90e32 could throw an AppError if the energy nonitor
        # is not communicating with the microcontroller.
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

        try:
            # Send reading needs the monitor id and db project id.
            # An exception will occur if we can't find either in the config file.
            s = SendReading()
            print('monitor name: {}.....project ID: {}'.format(
                s.monitor_name, s.project_id))
            while True:
                try:
                    # Check that monitor is working
                    sys0 = energy_sensor.sys_status0
                    if (sys0 == 0xFFFF or sys0 == 0):
                        raise OSError(SysStatusError().number,
                                      SysStatusError().explanation)
                    # Quick an dirty: Using the C channel.  BTW - A Channel
                    # doesn't want to work on this monitor.
                    power_reading = energy_sensor.active_power_C
                    current_reading = energy_sensor.line_currentC
                    s.send(power_reading, current_reading)
                    blink(led_green, 1)
                    time.sleep(TIME_BETWEEN_READINGS)
                except OSError as err:
                    if NoWiFiError().number == err.args[0]:
                        blink(led_red, NoWiFiError().blinks)
                        break
                    if SysStatusError().number == err.args[0]:
                        blink(led_red, SysStatusError().blinks)
                        break
        except OSError as err:
            if NoMonitorNameError().number == err.args[0]:
                blink(led_red, NoMonitorNameError().blinks)
            elif NoDBidError().number == err.args[0]:
                blink(led_red, NoDBidError().blinks)

    except OSError as err:
        # A calibration error means the microcontroller could not write over SPI...most likely the connection to the atm90e32 isn't right.
        # It could mean the monitor is not turned on or the SPI connections aren't right...
        if NoMonitor().number == err.args[0]:
            blink(led_red, NoMonitor().blinks)
        elif SysStatusError().number == err.args[0]:
            blink(led_red, SysStatusError().blinks)
        print('Error number: {}'.format(err.args[0]))
        print('Explanation: {}'.format(err.args[1]))
