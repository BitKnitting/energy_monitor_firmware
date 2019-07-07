# *******************************************************************************
# The MIT License (MIT)
#  Copyright (c) 2019, Margaret Johnson

#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# *******************************************************************************
# The wifi_connect library uses micropython's Access Point to get the SSID and
# password of the wifi this esp32 connects to.  Once the ESP32/nmicropython has
# connected to the wifi, it will know how to connect across reboots.  We use this code within the FitHome experience.
# Given the FitHome experience is for one month, we do not store the SSID and password.
# Rather, we assume the esp32/micropython are able to connect after the first
# wifi connection.
#

#
# *******************************************************************************
import network
import socket
import ure
import time
from collections import namedtuple

ap_ssid = "fithome_abc"
# Note: password length must be at least 8 characters: http://bit.ly/2XmxTgdz
ap_password = "fithome_abc"
ap_authmode = 3  # WPA2
Wifi_states = namedtuple(
    'Wifi_states', ['unknown', 'connected', 'not_connected'])
wifi_states = Wifi_states(0, 1, 2)
wifi_state = wifi_states.unknown

wlan_sta = network.WLAN(network.STA_IF)
wlan_ap = network.WLAN(network.AP_IF)

server_socket = None

def is_connected():
    wlan_sta.active(True)
    return True if wlan_sta.isconnected() else False

def get_connection():
    if isConnected():
        return True
    else:
        wifi_state = wifi_states.not_connected
        # Returns when connected to wifi.
        try_to_connect()
        wlan_ap.disconnect()
    return True


def do_connect(ssid, password):
    print('Trying to connect to %s...' % ssid)
    wlan_sta.connect(ssid, password)
    for retry in range(3):
        connected = wlan_sta.isconnected()
        if connected:
            return True
        time.sleep(0.1)
        # Print without a newline.
        print('.', end='')
    return False


def send_header(client, status_code=200, content_length=None):
    client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
    client.sendall("Content-Type: text/html\r\n")
    if content_length is not None:
        client.sendall("Content-Length: {}\r\n".format(content_length))
    client.sendall("\r\n")


def send_response(client, payload, status_code=200):
    content_length = len(payload)
    send_header(client, status_code, content_length)
    if content_length > 0:
        client.sendall(payload)
    client.close()

#  Display the SSIDs as well as a way to enter the wifi's password.


def handle_ssid_pwd_ui(client):
    ssids = sorted(set(ssid.decode('utf-8') for ssid, *_ in wlan_sta.scan()))
    send_header(client)
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


def handle_join_wifi(client, request):
    match = ure.search("ssid=([^&]*)&password=(.*)", request)

    if match is None:
        send_response(client, "Parameters not found", status_code=400)
        return False
    # version 1.9 compatibility
    try:
        ssid = match.group(1).decode(
            "utf-8").replace("%3F", "?").replace("%21", "!")
        password = match.group(2).decode(
            "utf-8").replace("%3F", "?").replace("%21", "!")
    except Exception:
        ssid = match.group(1).replace("%3F", "?").replace("%21", "!")
        password = match.group(2).replace("%3F", "?").replace("%21", "!")

    if len(ssid) == 0:
        send_response(client, "SSID must be provided", status_code=400)
        return False
    # We have the ssid and password.  Now we'll try to use this info to connect to the wifi.
    if do_connect(ssid, password):
        response = """\
            <html>
                <center>
                    <br><br>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            ESP successfully connected to WiFi network %(ssid)s.
                        </span>
                    </h1>
                    <br><br>
                </center>
            </html>
        """ % dict(ssid=ssid)
        send_response(client, response)
        wifi_state = wifi_states.connected
    else:
        response = """\
            <html>
                <center>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            ESP could not connect to WiFi network %(ssid)s.
                        </span>
                    </h1>
                    <br><br>
                    <form>
                        <input type="button" value="Go back!" onclick="history.back()"></input>
                    </form>
                </center>
            </html>
        """ % dict(ssid=ssid)
        send_response(client, response)
        return False
    return True


def handle_not_found(client, url):
    send_response(client, "Path not found: {}".format(url), status_code=404)


def stop():
    global server_socket

    if server_socket:
        server_socket.close()
        server_socket = None


def try_to_connect(port=80):
    global server_socket

    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]

    stop()
    wlan_ap.active(True)
    wlan_ap.config(essid=ap_ssid, password=ap_password, authmode=ap_authmode)
    server_socket = socket.socket()
    server_socket.bind(addr)
    print('listening....')
    server_socket.listen(1)

    print('Connect to WiFi ssid ' + ap_ssid +
          ', default password: ' + ap_password)
    print('and access the ESP via your favorite web browser at 192.168.4.1.')
    print('Listening on:', addr)

    while wifi_state != wifi_states.connected:

        client, addr = server_socket.accept()
        print('client connected from', addr)
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
            print("TAG is {}".format(tag))

            if tag == "":
                # Get the ssid and password.
                handle_ssid_pwd_ui(client)
                # Try to join the wifi.
            elif tag == "configure":
                handle_join_wifi(client, request)
            else:
                handle_not_found(client, url)

        finally:
            client.close()
