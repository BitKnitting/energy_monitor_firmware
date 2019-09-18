from wifi_connect import WifiAccess
from send_reading import SendReading

join_wifi = WifiAccess()
join_wifi.get_connected()
s = SendReading()
