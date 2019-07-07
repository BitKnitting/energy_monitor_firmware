from wifi_connect import get_connection
import network

if get_connection():
    pass # Turn LED to green.
    # Now that we have a connection, let's talk to the atm90e32.
