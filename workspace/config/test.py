from config import read_config, add_creds

monitor_name = read_config('monitor')
print(monitor_name)
add_creds('ssid', 'pwd')