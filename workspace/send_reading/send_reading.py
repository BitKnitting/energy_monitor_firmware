# *******************************************************************************
# The MIT License (MIT)
#  Copyright (c) 2019, Margaret Johnson

#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# *******************************************************************************
# The semd_reading library sends a power reading to the Firebase RT database.  It assumes
# The wifi connecton has already been made.  It uses the Firebase REST API to post
# the reading into the Firebase RT db.
#
# Required to know before using:
# The energy monitor's machine name.  This is given to the machine
#
#
# *******************************************************************************
import network
import urequests as requests
from wifi_connect import is_connected
import ujson as json
import uerrno
from app_error import AppError

CONFIG_FILE = 'lib/config.dat'


class SendReading:
    def __init__(self):
        try:
            with open(CONFIG_FILE) as f:
                lines = f.readlines()
                config_vars = json.loads(lines[0])
                self.machine_name = config_vars['machine']
                self.project_id = config_vars['project_id']
        except OSError as error:
            if error.args[0] == uerrno.ENOENT:
                raise OSError(
                    'An error occured trying to read {}'.format(CONFIG_FILE))
        except IndexError as error:
            raise IndexError(
                'Could not read variables from {}'.format(CONFIG_FILE))

    def send(self, power):
        # Assumes attached to wifi
        if not is_connected():
            raise AppError('Should be connected to wifi.')
        # .sv timestamp: http://bit.ly/2MO0XNt
        #data = '{'+'"V1":{},"V2":{},"I1":{},"I2":{},"P":{},".sv":"timestamp"'.format(v1,v2,i1,i2,power) +'}'
        data = '{'+'"P":{}'.format(power) + \
            ',"timestamp": {".sv":"timestamp"}}'
        print(data)
        path = 'https://' + self.project_id+'.firebaseio.com/' + \
            self.machine_name+'/'+'/.json'
        print(path)
        response = requests.post(path, data=data)
        print('response: {}'.format(response.text))
        return True
