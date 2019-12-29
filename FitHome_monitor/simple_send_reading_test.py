
from app_error import NoMonitor, SysStatusError, NoMonitorNameError, NoWiFiError, NoDBidError, blink
from wifi_connect import WifiAccess
from send_reading import SendReading

from atm90e32_u import ATM90e32
import time
import machine
# ***** Set up debug LEDs
# A red one for errors
# A green one for ok.

led_red = machine.Pin(27, machine.Pin.OUT)
led_green = machine.Pin(32, machine.Pin.OUT)
# ***** atm90e32 CALIBRATION SETTINGS *****/
lineFreq = 4485  # 4485 for 60 Hz (North America)
# 389 for 50 hz (rest of the world)
PGAGain = 21     # 21 for 100A (2x), 42 for >100A (4x)

VoltageGain = 42080  # 42080 - 9v AC transformer.
# 32428 - 12v AC Transformer

CurrentGainCT1 = 25498  # 38695 - SCT-016 120A/40mA
CurrentGainCT2 = 25498  # 25498 - SCT-013-000 100A/50mA
# 46539 - Magnalab 100A w/ built in burden resistor
# *******************************************/


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
        raise OSError(SysStatusError().number, SysStatusError().explanation)
    energy_sensor.line_voltageA
    energy_sensor.line_currentA
    # time.sleep(60)
    # blink(led_green, 5)
    join_wifi = WifiAccess()
    if join_wifi.get_connected():
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
                    iA = energy_sensor.line_voltageA
                    vA = energy_sensor.line_currentA
                    iC = energy_sensor.line_voltageC
                    vC = energy_sensor.line_currentC
                    pA = iA*vA
                    pC = iC*vC
                    print('vA: {} vC: {} iA: {} iC:{}'.format(vA, vC, iA, iC)
                    print('power A: {}, Power C: {}'.format(pA, pC))
                    # print('power: {}'.format(
                    #     energy_sensor.line_voltageA*energy_sensor.line_currentA))
                    print('everything works. ')
                    print('Active Power: {}'.format(
                        energy_sensor.active_power))
                    power_reading=pA+pC
                    s.send(power_reading)
                    blink(led_green, 1)
                    time.sleep(15)
                except OSError as err:
                    if NoWiFiError().number == err.args[0]:
                        blink(led_red, NoWiFiError().blinks)
                        break
                    if SysStatusError().number == err.args[0]:
                        blink(led_red, SysStatusError().blinks)
                        break
        except OSError as err:
            if NoMonitorameError().number == err.args[0]:
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
