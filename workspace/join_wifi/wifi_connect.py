# *******************************************************************************
# The MIT License (MIT)
#  Copyright (c) 2019, Margaret Johnson

#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# *******************************************************************************
# The wifi_connect library uses micropython's Access Point to get the SSID and
# password of thewifi this esp32 connects to.  Once the ESP32/nmicropython has
# connected to the wifi, it will know how to connect across reboots.  We use this
# code within the FitHome experience.
# Rather, we assume the esp32/micropython are able to connect after the first
# self.wifi connection.
#

#
# *******************************************************************************
import network
import socket
import ure
import time
from collections import namedtuple
from config import read_config, add_creds

ap_ssid = "fithome_abc"
# Note: password length must be at least 8 characters: http://bit.ly/2XmxTgdz
ap_password = "fithome_abc"
ap_authmode = 3  # WPA2


wlan_sta = network.WLAN(network.STA_IF)
wlan_ap = network.WLAN(network.AP_IF)


class WifiAccess:

    Wifi_states = namedtuple('Wifi_states', [
                             'connected', 'not_connected', 'wifi_info_no_good', 'no_ssid_pwd'])
    wifi_states = Wifi_states(0, 1, 2, 3)

    def __init__(self):
        wlan_sta.active(True)
        self.password = read_config('password')
        self.ssid = read_config('ssid')
        if (self.ssid == None or self.password == None):
            self.wifi_state = self.wifi_states.no_ssid_pwd
            print('>> We do not have an ssid and pwd yet.')
        else:
            self.wifi_state = self.wifi_states.not_connected

    # Connect if we can
    def get_connected(self):
        if self.wifi_state == self.wifi_states.connected:
            return True
        # have ssid and pwd, not connected.
        elif self.wifi_state == self.wifi_states.not_connected:
            wlan_sta.connect(self.ssid, self.password)
            while not wlan_sta.isconnected:
                pass
            print('>>We are connected.')
            # we are in the connected state
            self.wifi_state = self.wifi_states.connected
            return True
        # Become an Access Point
        else:
            print('>> We are becomming an Access Point')
            self._start_ap()

    def _do_connect(self):
        print('Trying to connect to {}...'.format(self.ssid))
        timeout = time.time() + 20   # try for 40 seconds
        wlan_sta.connect(self.ssid, self.password)
        while not wlan_sta.isconnected() and time.time() < timeout:
            time.sleep(0.1)
            print('.', end='')
        print('wifi connected: {}'.format(wlan_sta.isconnected()))
        if wlan_sta.isconnected():
            self.wifi_state = self.wifi_states.connected
            add_creds(self.ssid, self.password)
            print('\nConnected. Network config: ', wlan_sta.ifconfig())
            return True
        else:
            print('\nFailed. Not Connected to: ' + self.ssid)
            return False

    def _send_header(self, client, status_code=200, content_length=None):
        try:
            client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
            client.sendall("Content-Type: text/html\r\n")
            if content_length is not None:
                client.sendall("Content-Length: {}\r\n".format(content_length))
            client.sendall("\r\n")
        except OSError as error:
            print(error)
            print('Trying to send html to client, but unreachable.')

    def _send_response(self, client, payload, status_code=200):
        content_length = len(payload)
        self._send_header(client, status_code, content_length)
        if content_length > 0:
            client.sendall(payload)
        client.close()

    #  Display the SSIDs as well as a way to enter the self.wifi's password.

    def _handle_ssid_pwd_ui(self, client):
        ssids = sorted(set(ssid.decode('utf-8')
                           for ssid, *_ in wlan_sta.scan()))
        self._send_header(client)
        client.sendall("""\
            <html>
                <h1 style="color: #5e9ca0; text-align: center;">
                    <span style="color: #ff0000;">
                        Wi-Fi Client Setup
                    </span>
                </h1>
                <form action="configure" method="post">
                    <table style="margin-left: auto; margin-right: auto;">
                        <tbody>
        """)
        while len(ssids):
            ssid = ssids.pop(0)
            client.sendall("""\
                            <tr>
                                <td colspan="2">
                                    <input type="radio" name="ssid" value="{0}" />{0}
                                </td>
                            </tr>
            """.format(ssid))
        client.sendall("""\
                            <tr>
                                <td>Password:</td>
                                <td><input name="password" type="password" /></td>
                            </tr>
                        </tbody>
                    </table>
                    <p style="text-align: center;">
                        <input type="submit" value="Submit" />
                    </p>
                </form>
                <p>&nbsp;</p>
                <hr />
            </html>
        """)
        client.close()

    def _handle_join_wifi(self, client, request):
        match = ure.search("ssid=([^&]*)&password=(.*)", request)

        if match is None:
            self._send_response(
                client, "Parameters not found", status_code=400)
            return False
        # version 1.9 compatibility
        try:
            self.ssid = match.group(1).decode(
                "utf-8").replace("%3F", "?").replace("%21", "!")
            self.password = match.group(2).decode(
                "utf-8").replace("%3F", "?").replace("%21", "!")
            print('****ssid: {} password: {}'.format(self.ssid, self.password))
        except Exception:
            self.ssid = match.group(1).replace("%3F", "?").replace("%21", "!")
            self.password = match.group(2).replace(
                "%3F", "?").replace("%21", "!")

        if len(self.ssid) == 0:
            self._send_response(
                client, "SSID must be provided", status_code=400)
            return False
        # We have the ssid and password.  Now we'll try to use this info to connect to the self.wifi.
        if self._do_connect():
            response = """\
                <html>
                    <center>
                        <br><br>
                        <h1 style="color: #5e9ca0; text-align: center;">
                            <span style="color: #ff0000;">
                                ESP successfully connected to wifi network %(ssid)s.
                            </span>
                        </h1>
                        <br><br>
                    </center>
                </html>
            """ % dict(ssid=self.ssid)
            self._send_response(client, response)
        else:
            response = """\
                <html>
                    <center>
                        <h1 style="color: #5e9ca0; text-align: center;">
                            <span style="color: #ff0000;">
                                ESP could not connect to wifi network %(ssid)s.
                            </span>
                        </h1>
                        <br><br>
                        <form>
                            <input type="button" value="Go back!" onclick="history.back()"></input>
                        </form>
                    </center>
                </html>
            """ % dict(ssid=self.ssid)
            self._send_response(client, response)
            return False
        # No longer need access point.
        wlan_ap.active(False)
        return True

    def _handle_not_found(self, client, url):
        self._send_response(client, "Path not found: {}".format(
            url), status_code=404)

    def _stop(self, server_socket):

        if server_socket:
            server_socket.close()
            server_socket = None

    def _start_ap(self, port=80):
        wlan_ap.active(True)
        server_addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
        wlan_ap.config(essid=ap_ssid, password=ap_password,
                       authmode=ap_authmode)
        server_socket = socket.socket()
        server_socket.bind(server_addr)
        server_socket.listen(1)

        print('Connect to Access Point ' + ap_ssid +
              ', default password: ' + ap_password)
        print('and access the ESP via your favorite web browser at 192.168.4.1.')

        while self.wifi_state != self.wifi_states.connected and self.wifi_state != self.wifi_states.wifi_info_no_good:
            print('state: {}'.format(self.wifi_state))
            client, client_addr = server_socket.accept()
            print('client connected from', client_addr)
            try:
                client.settimeout(5.0)

                request = b""
                try:
                    while "\r\n\r\n" not in request:
                        request += client.recv(512)
                except OSError:
                    pass

                print("Request is: {}".format(request))
                if "HTTP" not in request:  # skip invalid requests
                    continue

                # version 1.9 compatibility
                try:
                    tag = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP",
                                     request).group(1).decode("utf-8").rstrip("/")
                except Exception:
                    tag = ure.search(
                        "(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).rstrip("/")
                if tag == "":
                    # Get the ssid and password.
                    self._handle_ssid_pwd_ui(client)
                    # Try to join the self.wifi.
                elif tag == "configure":
                    self._handle_join_wifi(client, request)
                else:
                    self._handle_not_found(client, tag)

            finally:
                client.close()
        self._stop(server_socket)
