
from atm90e32_u import ATM90e32
from app_error import NoMonitor, SysStatusError, NoMonitorNameError, NoWiFiError, NoDBidError, blink
import machine
import time


class MyTest:
    def __init__(self):
        self.led_red = machine.Pin(27, machine.Pin.OUT)
        self.led_green = machine.Pin(32, machine.Pin.OUT)
        # ***** atm90e32 CALIBRATION SETTINGS *****/

        lineFreq = 4485  # 4485 for 60 Hz (North America)
        # 389 for 50 hz (rest of the world)
        PGAGain = 21     # 21 for 100A (2x), 42 for >100A (4x)

        # VoltageGain = 42080  # 42080 - 9v AC transformer.
        VoltageGain = 37898  # What I calculated based on reading app notes on calibration
        # 32428 - 12v AC Transformer

        CurrentGainCT1 = 25368  # My calculation
        CurrentGainCT2 = 25368  # My calculation
        # CurrentGainCT1 = 25498  # 38695 - SCT-016 120A/40mA
        # CurrentGainCT2 = 25498  # 25498 - SCT-013-000 100A/50mA
        # 46539 - Magnalab 100A w/ built in burden resistor
        # *******************************************/
        try:
            # Get reading and then send reading.
            # Initializing the atm90e32 could throw an AppError if the energy monitor
            # is not communicating with the microcontroller.
            self.energy_sensor = ATM90e32(lineFreq, PGAGain,
                                          VoltageGain, CurrentGainCT1, 0, CurrentGainCT2)
            time.sleep(.5)
            # Maybe we don't have to initialize a second time...I found working with a
            # different atm90 that initializing twice was more robust than once.
            self.energy_sensor = ATM90e32(lineFreq, PGAGain,
                                          VoltageGain, CurrentGainCT1, 0, CurrentGainCT2)

            # We have an instance of the atm90e32.  Let's check if we get sensible readings
            sys0 = self.energy_sensor.sys_status0
            if (sys0 == 0xFFFF or sys0 == 0):
                raise OSError(SysStatusError().number,
                              SysStatusError().explanation)
        except OSError as e:
            blink(self.led_red, 4)
            print(e)
            print(e.args)
        else:
            blink(self.led_green, 2)

    def get_power(self):
        vA = self.energy_sensor.line_voltageA
        iA = self.energy_sensor.line_currentA
        vC = self.energy_sensor.line_voltageC
        iC = self.energy_sensor.line_currentC
        pA = iA*vA
        pC = iC*vC
        print('vA: {} vC: {} iA: {} iC:{} pA {} pC {}'.format(
            vA, vC, iA, iC, pA, pC))
        power_reading = self.energy_sensor.active_power_A+self.energy_sensor.active_power_C
        current_reading = self.energy_sensor.line_currentA+self.energy_sensor.line_currentC

        print('Power reading to db: {} Current reading to db: {}'.format(
            power_reading, current_reading))
