
from atm90e32_u import ATM90e32
import time


try:
    # raise OSError(app_error.CALIBRATION_ERROR,
    #               "Calibration failed.  Could not write to registers.")
    # Get reading and then send reading.
    # Initializing the atm90e32 could throw an AppError if the energy nonitor
    # is not communicating with the microcontroller.
    energy_sensor = ATM90e32(4485, 21, 42080, 25498, 0, 25498)
    time.sleep(.5)
    energy_sensor = ATM90e32(4485, 21, 42080, 25498,0, 25498)
    time.sleep(1)
    # Kick the atm into power readings....
    vA = energy_sensor.line_voltageA
    iA = energy_sensor.line_currentA
    pA = vA*iA
    print('voltage A: {} current A: {} power A: {}'.format(vA, iA, pA))
    vC = energy_sensor.line_voltageC
    iC = energy_sensor.line_currentC
    pC = vC*iC
    print('voltage C: {} current C: {} power C: {}'.format(vC, iC, pC))
    print('total power: {}'.format(pA+pC))
    # Now let's see what we get from the power registers.
    # We are interested in Active Power since this is the kWh we get billed.
    # First Total (All phase sum) Active Power
    print("Total active power: {}".format(energy_sensor.total_active_power))
    # Now for the two phases = A and C for us NA folks.
    print("Power A: {} Power C: {} Power Total: {}".format(energy_sensor.active_power_A,
                                                           energy_sensor.active_power_C, energy_sensor.active_power_A+energy_sensor.active_power_C))


except OSError as e:
    print(e)
    print(e.args)

