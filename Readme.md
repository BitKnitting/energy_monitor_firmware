# Energy Monitor Firmware
The purpose of this project is to build the micropython code used by the energy monitor to:  
* Join the homeowner's wifi.  
* Send readings to the Firebase RT db.
# Preparing the ESP32
At least for testing, we are using [the ESP32 DevKit C](https://amzn.to/2JInYgj).  For the IDE we are using [uPyCraft](http://docs.dfrobot.com/upycraft/). 
* Download the
* Install and open uPyCraft.  
* The ESP32 most likely does not have a build of micropython, or you need to update the build.  If a dialog box does not come up immediately, select  Tools->BurnFirmware.  [This is the micropython build we currently use.](micropython_build/esp32-20190529-v1.11.bin).  For ESP32 micropython firmware, the settings should be:
![micropython burn firmware dialog](imgs/uPyCraft_burnimage_dialog.png)  
* 
# Join the Homeowner's Wifi
Soon after the electrician installs and activates the energy monitor, the home owner must tell the energy monitor the home wifi SSID and password. The technique to do this is starting the energy monitor's firmware as a Local Access Point.  The homeowner goes to their mac or pc and scrolls the available wifi networks.  Once the energy monitor is plugged in, the network __fithome_abc__ will be added. 
The home owner:    
* goes to their mac or pc.  
* opens the drop down list of wifi networks and chooses __fithome_abc__.
* uses __fithome_abc__ for the password.
* opens a browser and types in the address ```192.168.4.1```
* A web page is shown where the user picks their wifi SSID and enters the password.  
## micropython code
The code file for connecting to the wifi is [wifi_connect.py](workspace/join_wifi/wifi_connect.py).
  
After successful completion, the energy monitor is able to use the home's wifi.
  
__NOTE: The energy monitor will not be able to proceed unless there is a constant connection.__  
# Sending Readings to Firebase RT db
Before sending readings, [send_reading.py](workspace/send_reading/send_reading.py) needs configuration info stored in the config.dat file.
## Config File
The config file, [config.dat](workspace/config/config.dat), contains:  
* The __machine name__ of the energy monitor.  The machine name is made up of a common name and the date the machine was assigned to a FitHome member.  The machine name used for testing has the common name of 'bambi' and date of '07052019' = ```bambi-07052019```.  
* The __Firebase RT Project ID__ found in the firebase console for the FitHome project:  
![project id page](imgs/project_id_page.png)
## Rest API
The energy monitor uses the Firebase REST APIs to send readings to the Firebase RT db.  An example curl command:  
```
curl -X POST -d '{"P":1127.9}' \
  'https://<Firebase project name>.firebaseio.com/<machine name>/.json' 
```
### Curl to HTTP Post
The firmware uses HTTP.  I found this great web page that [converts curl commands to Python  ](https://curl.trillworks.com/).  VERY HELPFUL.
### Example post
For example, this code would send the power value to the Firebaase RT db that is attached to the iot-test-1e426 project:  
```
    def send_reading(self, v1, v2, i1, i2, power):
        do_connect(self.ssid, self.password)
        # .sv timestamp: http://bit.ly/2MO0XNt
        #data = '{'+'"P":{},".sv":"timestamp"'.format(power) +'}'
        data = '{'+'"P":{}'.format(power) +',"timestamp": {".sv":"timestamp"}}'
        path = 'https://iot-test-1e426.firebaseio.com/'+self.device_name+'/'+self.userID+'/.json'
        print(path)
        response = requests.post(path, data=data)
        print('response: {}'.format(response.text))
```
The power reading is sent.  The "timestamp" is generated on the Firebase server then filled into the db entry.
# Reading Power Values from the Energy Monitor
We are using the [Split Single Phase Energy Meter](https://circuitsetup.us/index.php/product/split-single-phase-real-time-whole-house-energy-meter-v1-2/) to get a home's power values.  
  
## Thanks to Those That Went Before

There is _so much_ prior work that made it easier to write a CP library for the atm90e32.  Efforts include:   
* Circuit Setup's [Split Single Phase Energy Meter](https://circuitsetup.us/index.php/product/split-single-phase-real-time-whole-house-energy-meter-v1-2/).  I am delighted that John is providing us with this open source energy monitor!  It makes it easy to figure out how much electricity is being used.  Thank you John.  Thank you for helping me get started with your product.
* Tisham Dhar's [atm90e26 Arduino library](https://github.com/whatnick/ATM90E26_Arduino).   Tisham deserves a HUGE THANK YOU for his open source atm90e* hw and sw design. Tisham's excellent work and friendly help are inspirational.
* The [atm90e26 Circuit Python library I wrote](https://github.com/BitKnitting/HappyDay_ATM90e26_CircuitPython)  
* Circuit Setup's [atm90e32 Arduino library](https://github.com/CircuitSetup/Split-Single-Phase-Energy-Meter/tree/master/Software/libraries/ATM90E32)

## ESP32 DevKitC
Here is an image of the pinout:  
![esp32 devkitc pinout](https://i1.wp.com/randomnerdtutorials.com/wp-content/uploads/2018/08/ESP32-DOIT-DEVKIT-V1-Board-Pinout-36-GPIOs-updated.jpg?ssl=1)    
This image is better than most because it points out what GPIO pins to stay away from when setting up a GPIO pin for output, as we do for the LEDs.

### Wiring SPI
With this board I wired HSPI. [From the micropython forum](https://forum.micropython.org/viewtopic.php?t=3386), Native SPI pins are (clk, mosi, miso, cs):   
SPI1: 6, 8, 7, 11  
HSPI: 14,13,12,15  
VSPI: 18,23,19, 5  
If using native pins, the maximum SPI clock can be set to 80 MHZ.
#### HSPI  
Looking at [the micropython esp32 docs for SPI](https://docs.micropython.org/en/latest/esp32/quickref.html#hardware-spi-bus), we'll use HW SPI (id=1):  
* GPIO 14 - SCK  
* GPIO 13 - MOSI  
* GPIO 12 - MISO (HSPI Q)

The image notes that GPIO 15 is HW CS.  
For HSPI:  
```
from machine import Pin, SPI 
hspi = SPI(1, 200000, sck=Pin(14), mosi=Pin(13), miso=Pin(12))  
```
#### VSPI
Some boards - such as the esp32 wemos  
![esp32 wemos pinout](https://i.imgur.com/JIXyBAU.jpg)    

This board has grouped pins to make it "easier" to wire for VSPI: 
VSPI: 18,23,19, 5
* GPIO 18 - SCK  
* GPIO 19 - MISO 
* GPIO 23 - MOSI  
* GPIO 5  - CS

For VSPI:  
```
vspi = SPI(2, baudrate=200000, polarity=0, phase=0, bits=8, firstbit=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
```
### Wiring LEDs
We decided on two LEDs, a red one for errors, and a green one to let us know the monitor is working.  According to the pinout above, the pins to stay away from are:  
*  GPIO6-11  
*  We need output pins, so don't use GPIO36,39,34,35 because they are input only.