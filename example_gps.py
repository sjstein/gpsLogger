from gps import *
import time

running = True


def getPositionData(gpsd):
    nx = gpsd.next()
    # For a list of all supported classes and fields refer to:
    # https://gpsd.gitlab.io/gpsd/gpsd_json.html
    if nx['class'] == 'TPV':
        latitude = getattr(nx,'lat', "Unknown")
        longitude = getattr(nx,'lon', "Unknown")
        print(f'Your position: lon = {longitude} , lat = {latitude}')


gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

try:
    print('Program started')
    while running:
        getPositionData(gpsd)
        time.sleep(1.0)

except (KeyboardInterrupt):
    running = Falsek
    print('Program complete')