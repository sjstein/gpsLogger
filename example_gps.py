from gps import *
import time

running = True


def getPositionData(gpsd):
    nx = gpsd.next()
    # For a list of all supported classes and fields refer to:
    # https://gpsd.gitlab.io/gpsd/gpsd_json.html
    if nx['class'] == 'TPV':
        latitude = getattr(nx, 'lat', "Unknown")
        longitude = getattr(nx, 'lon', "Unknown")
        gps_time = getattr(nx, 'time', "Unknown")
        print(f'At {gps_time}, your position: lat = {latitude} , lon = {longitude}')

    if nx['class'] == 'SKY':
        sat_time = getattr(nx, 'time', "")
        satellites = getattr(nx, 'satellites', "")
        print(f'Found {len(satellites)} satellites with the following info:')
        for satellite in satellites:
            print(f'ID#{satellite.PRN}, at {satellite.az}N and elevation {satellite.el}, s/n: '
                  f'{satellite.ss} @ {sat_time}')


gpsd = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)

try:
    print('Program started')
    while running:
        getPositionData(gpsd)
        time.sleep(1.0)

except (KeyboardInterrupt):
    running = False
    print('Program complete')
