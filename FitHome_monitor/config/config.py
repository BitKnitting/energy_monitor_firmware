import ujson as json
from app_error import NoConfigFile
#
# The config files are found in the lib subdir.  main passes in
# the config filename for the monitor that will be started up with
# main's execution.
CONFIG_FILE = 'lib/config.json'


def exists_config():
    try:
        open(CONFIG_FILE)
    except (OSError, KeyError, IndexError) as error:
        raise OSError(NoConfigFile().number, NoConfigFile().explanation)


def read_config(key):
    try:
        with open(CONFIG_FILE) as f:
            config_vars = json.load(f)
            return config_vars[key]
    except (OSError, KeyError, IndexError) as error:
        print('An error occured trying to read the key {} in {}.'.format(
            key, CONFIG_FILE))
        return None


def add_creds(s, p):
    config_vars = {}
    # Open for reading.
    try:
        with open(CONFIG_FILE) as f:
            config_vars = json.load(f)
    except (OSError, KeyError, IndexError) as error:
        print('An error occured trying to read config.json')
        return None
    else:
        # Open for writing
        config_vars['ssid'] = s
        config_vars['password'] = p
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_vars, f)
        except (OSError, KeyError, IndexError) as error:
            print('An error occured trying to write to config.json')
            return None
