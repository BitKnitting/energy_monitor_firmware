from send_reading import SendReading
from app_error import AppError
try:
    s = SendReading()
    print('machine name: {}.....project ID: {}'.format(
        s.machine_name, s.project_id))
    s.send(1137.8)
    print('it worked: {}'.format(it_worked))
except OSError as err:
    print(err.args)
except AppError as err:
    print(err.args)

