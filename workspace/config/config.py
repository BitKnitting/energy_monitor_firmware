import ujson as json
#import json

CONFIG_FILE = 'lib/config.json'


def read_config(key):

    with open(CONFIG_FILE) as f:
        try:
            config_vars = json.load(f)
            return config_vars[key]
        except (OSError, KeyError, IndexError) as error:
            print('An error occured trying to read the key {} in {}.'.format(
                key, CONFIG_FILE))
            return None


def add_creds(s, p):
    config_vars = {}
    with open(CONFIG_FILE) as f:
        try:
            config_vars = json.load(f)
        except:
            print('An error occured trying to read config.json')
            return None
    config_vars['ssid'] = s
    config_vars['password'] = p
    with open(CONFIG_FILE, 'w') as f:
        try:
            json.dump(config_vars, f)
        except:
            print('An error occured trying to read config.json')
            return None
