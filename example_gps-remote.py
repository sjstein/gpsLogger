from gps import *
import time
import datetime
getTPV = True
getSKY = False

running = True

retries = 0


def getPositionData():
    global getTPV, getSKY
    poll = True
    gpsd = gps(host='192.168.1.121', port='2947', mode=WATCH_ENABLE | WATCH_NEWSTYLE)
    while poll is True:
        nx = gpsd.next()
        print(f'found class = {nx["class"]}')
        # For a list of all supported classes and fields refer to:
        # https://gpsd.gitlab.io/gpsd/gpsd_json.html
        if nx['class'] == 'TPV' and getTPV is True:
            latitude = getattr(nx, 'lat', "Unknown")
            longitude = getattr(nx, 'lon', "Unknown")
            gps_time = getattr(nx, 'time', "Unknown")
            sys_time = datetime.datetime.now()
            print(f'Position: lat = {latitude} , lon = {longitude}')
            print(f'System time: {sys_time}')
            print(f'GPS time   : {gps_time}')
            sysplit = str(sys_time).split(':')
            sysec = sysplit[2].split('.')[0]
            symin = sysplit[1]
            gpsplit = gps_time.split(':')
            gpsec = gpsplit[2].split('.')[0]
            gpmin = gpsplit[1]
            difmin = int(gpmin) - int(symin)
            difsec = int(gpsec) - int(sysec)
            print(f'Time difference (MIN:SEC) = {difmin}:{difsec}')

            print(f'\nRetries so far: {retries}\n')
            time.sleep(5)
            getTPV = False
            getSKY = True

        if nx['class'] == 'SKY' and getSKY is True:
            sat_time = getattr(nx, 'time', "")
            satellites = getattr(nx, 'satellites', "")
            print(f'Found {len(satellites)} satellites with the following info:')
            for satellite in satellites:
                print(f'ID#{satellite.PRN}, at {satellite.az}N and elevation {satellite.el}, s/n: '
                      f'{satellite.ss} @ {sat_time}')
            print()
            poll = False
            # Closing the gpsd connection causes the the daemon to flush the serial buffer
            #  which ensures the next time we want to read, we get recent gps data.
            getSKY = False
            getTPV = True
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


