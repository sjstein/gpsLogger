from gps import *
import time
import datetime
getTPV = True

running = True

retries = 0

#gpsd = gps(host='192.168.1.121', port='2947', mode=WATCH_ENABLE | WATCH_NEWSTYLE)

def getPositionData():
    global getTPV
    poll = True
    gpsd = gps(host='192.168.1.121', port='2947', mode=WATCH_ENABLE | WATCH_NEWSTYLE)
    while poll is True:
        nx = gpsd.next()
        # For a list of all supported classes and fields refer to:
        # https://gpsd.gitlab.io/gpsd/gpsd_json.html
        if nx['class'] == 'TPV' and getTPV is True:
            latitude = getattr(nx, 'lat', "Unknown")
            longitude = getattr(nx, 'lon', "Unknown")
            gps_time = getattr(nx, 'time', "Unknown")
            print(f'Position: lat = {latitude} , lon = {longitude}')
            print(f'System time: {datetime.datetime.now()}')
            print(f'GPS time   : {gps_time}')
            print(f'\nRetries so far: {retries}\n')
            time.sleep(5)
            getTPV = False

        if nx['class'] == 'SKY':
            sat_time = getattr(nx, 'time', "")
            satellites = getattr(nx, 'satellites', "")
            getTPV = True
            print(f'Found {len(satellites)} satellites with the following info:')
            for satellite in satellites:
                print(f'ID#{satellite.PRN}, at {satellite.az}N and elevation {satellite.el}, s/n: '
                      f'{satellite.ss} @ {sat_time}')
            print()
            poll = False
            gpsd.close()


while True:
    try:
        print('Program started')
        while running:
            getPositionData()
            time.sleep(1.0)

    except KeyboardInterrupt:
        running = False
        print('Program complete')
        break

    except ConnectionError:
        print(f'\nTrapped connection error - closing then retry\n')
        retries += 1
        time.sleep(1.0)
        running = True


