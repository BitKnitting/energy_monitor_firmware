import time


class NoMonitor():
    # When the atm class is initialized, it writes calibration info to
    # registers.  This error means the microcontroller couldn't write to
    # the atm.  Most likely the monitor isn't plugged in or the SPI
    # connection isn't working properly.
    number = 301
    explanation = 'Could not contact a monitor.'
    blinks = 1


class SysStatusError():
    # After initializing the atm90e32, we read the system status register.
    # The results we got lead us to believe the monitor isn't working right.
    # Blinks are set to 0 to say just keep blinking...over and over...until someone
    # sees it.
    number = 302
    explanation = 'The system status register value was bad.'
    blinks = 0


class NoWiFiError():
    # We're trying to send readings but we're not connected to wifi.
    # Connecting to wifi happens before sending readings, so something
    # is off.
    number = 303
    explanation = "Can't connect to WiFi."
    blinks = 3


class NoMonitorNameError():
    # The monitor name should be in config.json - but we didn't find it
    # there.  It is needed to write readings.
    number = 304
    explanation = "Can't retrieve monitor name."
    blinks = 4


class NoDBidError():
    # The Firebase project id msut be in config.json - but we didn't find it
    # there.  It is needed to write readings.
    number = 305
    explanation = "Can't retrieve the database project id."
    blinks = 5


class NoConfigFile():
    # A config file containing the monitor name and Firebase project id
    # must exist.
    number = 306
    explanation = "Config file does not exist."
    blinks = 2


def blink(led, nTimes):
    print('IN BLINK. blinking: {} times'.format(nTimes))
    secs_to_blink = 1
    if nTimes == 0:
        while True:
            led.on()
            time.sleep(secs_to_blink)
            led.off()
            time.sleep(secs_to_blink)
    else:
        for _ in range(nTimes):
            print('blinking')
            led.on()
            time.sleep(secs_to_blink)
            led.off()
            time.sleep(secs_to_blink)
