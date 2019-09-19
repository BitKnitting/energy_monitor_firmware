from wifi_connect import WifiAccess
from send_reading import SendReading

join_wifi = WifiAccess()
join_wifi.get_connected()
s = SendReading()
s.send(101.2)
s.send(98.0)
s.send(989.0)