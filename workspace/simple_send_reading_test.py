from wifi_connect import WifiAccess
from send_reading import SendReading
from app_error import AppError
from atm90e32_u import ATM90e32
import time

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
    join_wifi = WifiAccess()
    if join_wifi.get_connected():
        # Get reading and then send reading.
        energy_sensor = ATM90e32(lineFreq, PGAGain,
                                 VoltageGain, CurrentGainCT1, 0, CurrentGainCT2)
        s = SendReading()
        print('machine name: {}.....project ID: {}'.format(
            s.machine_name, s.project_id))
        while True:
            power_reading = energy_sensor.active_power
            s.send(power_reading)
            time.sleep(15)
except OSError as err:
    print(err.args)
except AppError as err:
    print(err.args)
