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
    # import dummy data server
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
    msg_head = '|' + str(tname) + '| '  # Create message header with thread ID
    while not shutdown.is_set():
        try:
            data = conn.recv(160)

        except OSError as msg:
            # This exception will cover various socket errors such as a broken pipe (client disconnect)
            log.erro(msg_head + 'Unexpected error (' + str(msg) + ') connection closed from client : ' +
                     str(addr), fname)
            conn.close()
            return -1

        if str(data.decode('utf-8')).startswith(MSG_READ_POS):
            log.info(msg_head + 'READ_POS request from client : ' + str(addr), fname)
            try:
                nx = gpsd.next()
                # For a list of all supported classes and fields refer to:
                # https://gpsd.gitlab.io/gpsd/gpsd_json.html
                while nx['class'] != 'TPV':     # Wait for the proper message to roll around
                    time.sleep(0.5)
                    nx = gpsd.next()
                    # Need a timeout escape
                latitude = getattr(nx, 'lat', "Unknown")
                longitude = getattr(nx, 'lon', "Unknown")
                data = str(latitude) + ',' + str(longitude)
                log.info(msg_head + 'Server sent: ' + data, fname)
                conn.send(data.encode())

            except OSError as msg:
                # This exception will cover various socket errors such as a broken pipe (client disconnect)
                log.erro(msg_head + 'Unexpected error (' + str(msg) + ') connection closed from client : '
                         + str(addr), fname)
                conn.close()
                return -1

        elif str(data.decode('utf-8')).startswith(MSG_DISCONNECT):
            log.info(msg_head + 'DISCONNECT requested from client : ' + str(addr), fname)
            conn.close()
            log.info(msg_head + 'Client ' + str(addr) + ' : connection closed', fname)
            return 1

        else:
            try:
                log.warn(msg_head + 'Unknown command received from client : ' + str(addr) + ' [' +
                         data.decode('utf-8') + ']', fname)
                response = 'CMD_UNKNOWN : ' + data.decode('utf-8')
                conn.send(response.encode())

            except OSError as msg:
                # This exception will cover various socket errors such as a broken pipe (client disconnect)
                log.erro(msg_head + 'Unexpected error (' + str(msg) + ') connection closed from client : ' +
                         str(addr), fname)
                conn.close()
                return -1


# Main program begins

MSG_READ_POS = 'r pos'
MSG_DISCONNECT = 'discon'
MAXTID = 999  # Maximum TID
tid = 0  # Thread ID number

# Open port to accept remote requests
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, port))
    s.listen(1)

    # connect to gps daemon
    gpsd = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)

    # Open logging file (append mode) and write header
    fname = str(date.today()) + '_gpsServer.log'
    log.info('|SUPR| Server started : ' + HOST + '(' + str(port) + ')', fname)

    retry = 2  # Timer for retries

    # Main loop
    shutdown_event = threading.Event()
    while True:
        try:
            log.info('|SUPR| waiting for new client connection...', fname)
            connection, address = s.accept()  # Wait for connection request from client
            log.info('|SUPR| Connection accepted from : ' + str(address), fname)
            t = threading.Thread(target=threaded_client, args=(connection, address, shutdown_event),
                                 name='T' + str(tid).zfill(3))
            t.start()
            tid += 1
            if tid > MAXTID:
                tid = 0
            log.info('|SUPR| Current number of client threads : {0}'.format(str(threading.activeCount() - 1)), fname)
        except KeyboardInterrupt:
            log.warn('|SUPR| Server halting due to user intervention.')
            log.warn(f'|SUPR| Stopping {threading.activeCount()-1} child thread(s).')
            shutdown_event.set()
            exit(0)
