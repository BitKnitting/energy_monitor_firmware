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

from app_error import AppError
from config import read_config

CONFIG_FILE = 'lib/config.json'


class SendReading:
    def __init__(self):
        self.machine_name = read_config('machine')
        if self.machine_name is None:
            raise AppError('There is no machine name.')
        self.project_id = read_config('project_id')
        if self.project_id is None:
            raise AppError('There is no Firebase project id.')

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
