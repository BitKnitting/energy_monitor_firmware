import ujson as json

CONFIG_FILE = 'lib/config.json'


def read_config(key):

    with open(CONFIG_FILE) as f:
        try:
            lines = f.readlines()
            config_vars = json.loads(lines[0])
            return config_vars[key]
        except (OSError, KeyError, IndexError) as error:
            print('An error occured trying to read the key {}.'.format(key))
            return None


def add_creds(ssid, password):
    config_vars = {}
    with open(CONFIG_FILE) as f:
        lines = f.readlines()
        config_vars = json.loads(lines[0])
    config_vars['ssid'] = ssid
    config_vars['password'] = password
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_vars, f)
