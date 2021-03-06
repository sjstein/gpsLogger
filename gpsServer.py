#!/usr/bin/python3
# take the cr out
# Built-in packages:
from argparse import ArgumentParser
from datetime import date
import socket
import sys
import threading

# Project-locals:
from aspLibs.aspUtilities import get_interface_devices, IntRange
from aspLibs.aspUtilities import V_HIGH
from aspLibs.aspUtilities import AspLogger

PORT_LOW = 5000
PORT_HIGH = 5050
PORT_DEFAULT = 5015

RETRY_MAX = 10     # Maximum number of retries before returning a value of UNKNOWN to clien

log = AspLogger(V_HIGH)

parser = ArgumentParser()
parser.add_argument('--debug',
                    action='store_true',
                    help='When set, use synthetic data')
parser.add_argument('-i',
                    '--interface',
                    default='eth0',
                    dest='interface',
                    help='Interface device name to use')
parser.add_argument('-p', '--port',
                    default=PORT_DEFAULT,
                    dest='port',
                    type=IntRange(PORT_LOW, PORT_HIGH),
                    help='Port number to listen on')
args = parser.parse_args()
port = args.port

# Conditionally import mock or hardware sensor module:
if args.debug:
    log.disp('\n    *** WARNING ***     ')
    log.disp('Operating in DEBUG mode!')
    log.disp(' USING MOCK SENSOR DATA \n')
    # import dummy data server here - TBD
    log.disp('**NOTE** THIS IS NO CURRENTLY IMPLEMENTED')
else:
    from gps import *

# Retrieve all interface device infos:
interface_info = get_interface_devices()

# If the command line arg device is not found, error out:
HOST = interface_info.get(args.interface)
if HOST is None:
    log.erro(f'Device {args.interface} not found.')
    log.disp('\tAvailable interfaces:')
    for interface, address in interface_info.items():
        log.disp(f'\t\t{interface} : {address}')
    log.erro('Exiting')
    sys.exit(-1)


# Client handler - meant to be threaded
def threaded_client(conn, addr, shutdown):
    tname = threading.current_thread().name
    msg_head = '|' + str(tname) + '|'  # Create message header with thread ID
    while not shutdown.is_set():
        try:
            data = conn.recv(160)
            gpsd = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)  # Open (local) connection to gps daemon
            loopcount = 0   # Counter to escape from too many reads from gps daemon

        except OSError as msg:
            # This exception will cover various socket errors such as a broken pipe (client disconnect)
            log.erro(f'{msg_head} Unexpected error ({msg}) connection closed from client: {addr}', fname)
            conn.close()
            return -1

        if str(data.decode('utf-8')).startswith(MSG_READ_POS):
            log.info(f'{msg_head} READ_POS request from client: {addr}', fname)
            try:
                nx = gpsd.next()
                # For a list of all supported classes and fields refer to:
                # https://gpsd.gitlab.io/gpsd/gpsd_json.html
                while nx['class'] != 'TPV':     # Wait for the proper message to roll around
                    time.sleep(0.5)
                    nx = gpsd.next()
                    loopcount += 1
                    if loopcount > RETRY_MAX:
                        log.info(f'{msg_head} Read timeout from gps daemon', fname)
                        break
                gps_time = getattr(nx, 'time', "Unknown")
                latitude = getattr(nx, 'lat', "Unknown")
                longitude = getattr(nx, 'lon', "Unknown")
                data = f'{gps_time},{latitude},{longitude}'
                log.info(f'{msg_head} Server sent: {data}', fname)
                conn.send(data.encode())
                gpsd.close()

            except OSError as msg:
                # This exception will cover various socket errors such as a broken pipe (client disconnect)
                log.erro(f'{msg_head} Unexpected error ({msg}) connection closed from client: {addr}', fname)
                conn.close()
                gpsd.close()
                return -1

        elif str(data.decode('utf-8')).startswith(MSG_READ_SAT):
            log.info(f'{msg_head} SAT_INFO request from client: {addr}', fname)
            try:
                nx = gpsd.next()
                # For a list of all supported classes and fields refer to:
                # https://gpsd.gitlab.io/gpsd/gpsd_json.html
                while nx['class'] != 'SKY':     # Wait for the proper message to roll around
                    time.sleep(0.5)
                    nx = gpsd.next()
                    # Need a timeout escape
                    loopcount += 1
                    if loopcount > RETRY_MAX:
                        log.info(f'{msg_head} Read timeout from gps daemon', fname)
                        break
                sat_time = getattr(nx, 'time', "")
                satellites = getattr(nx, 'satellites', "")
                num_sat = len(satellites)
                log.info(f'{msg_head} Found {num_sat} satellites')
                conn.send(sat_time.encode())    # Send GPS time info from this record
                msg = ''
                for satellite in satellites:
                    msg += f'{satellite.PRN},{satellite.az},{satellite.el},{satellite.ss}|'
                    # data in format : Sat #, azimuth, elevation, s/n ratio
                msg = msg[:-1]  # Remove trailing delimiter
                log.info(f'{msg_head} Server sent: {msg}', fname)
                conn.send(msg.encode())
                gpsd.close()

            except OSError as msg:
                # This exception will cover various socket errors such as a broken pipe (client disconnect)
                log.erro(f'{msg_head} Unexpected error ({msg}) connection closed from client: {addr}', fname)
                conn.close()
                gpsd.close()
                return -1

        elif str(data.decode('utf-8')).startswith(MSG_DISCONNECT):
            log.info(f'{msg_head} DISCONNECT requested from client: {addr}', fname)
            conn.close()
            log.info(f'{msg_head} Connection closed from client: {addr}', fname)
            return 1

        else:
            try:
                log.warn(f'{msg_head} Unknown command received from client: {addr} [{data.decode("utf-8")}]', fname)
                response = 'CMD_UNKNOWN : ' + data.decode('utf-8')
                conn.send(response.encode())

            except OSError as msg:
                # This exception will cover various socket errors such as a broken pipe (client disconnect)
                log.erro(f'{msg_head} Unexpected error ({msg}) connection closed from client: {addr}', fname)
                conn.close()
                return -1


# Main program begins

MSG_READ_POS = 'r pos'
MSG_READ_SAT = 'r sat'
MSG_DISCONNECT = 'discon'

MAXTID = 999  # Maximum TID
tid = 0  # Thread ID number

# Open port to accept remote requests
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, port))
    s.listen(1)

    # Open logging file (append mode) and write header
    fname = str(date.today()) + '_gpsServer.log'
    log.info(f'|SUPR| Server started : {HOST} ({port})', fname)

    retry = 2  # Timer for retries

    # Main loop
    shutdown_event = threading.Event()
    while True:
        try:
            log.info('|SUPR| Waiting for new client connection...', fname)
            connection, address = s.accept()  # Wait for connection request from client
            log.info(f'|SUPR| Connection accepted from : {address}', fname)
            t = threading.Thread(target=threaded_client, args=(connection, address, shutdown_event),
                                 name='T' + str(tid).zfill(3))
            t.start()
            tid += 1
            if tid > MAXTID:
                tid = 0
            log.info(f'|SUPR| Current number of client threads: {threading.activeCount() - 1}', fname)
        except KeyboardInterrupt:
            log.warn('|SUPR| Server halting due to user intervention.')
            log.warn(f'|SUPR| Stopping {threading.activeCount()-1} child thread(s).')
            shutdown_event.set()
            exit(0)
