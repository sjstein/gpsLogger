import argparse
import socket
import time
import sys

# Project-locals
from aspLibs.aspUtilities import valid_ip, IntRange, retry_connect
from aspLibs.aspUtilities import V_NONE, V_HIGH
from aspLibs.aspUtilities import AspLogger


# Variable declaration section
archive_freq = 5    # Default archive frequency in seconds
run_time = 60       # Default run time in minutes
logging = False     # Default to no logging
accum_time = 0      # Counter to hold total run time
depth_meters = 0.0
depth_feet = 0.0
temp_c = 0.0
temp_f = 0.0
f = ''  # file object
s = ''  # socket object
data = ''  # Return string from server
curr_time = ''
curr_date = ''

prog_name = '{' + sys.argv[0] + '}'

# Constants
PORT_LOW = 5000
PORT_HIGH = 5050
PORT_DEFAULT = 5015

GPSD_PORT = 2947

MSG_READ_POS = b'r pos'
MSG_READ_SAT = b'r sat'
MSG_DISCONNECT = b'discon'

# Set up argument parser
parser = argparse.ArgumentParser(description='Python script to query a remote server for GPS data\
 data, and optionally write that data to a text file.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('serverIP', help='IP Number of server.')
parser.add_argument('-l', '--log', help='File name for logging (default is NO logging).')
parser.add_argument('-f', '--freq', help='Frequency (in seconds) to read data.',
                    type=IntRange(1,), default=archive_freq)
parser.add_argument('-t', '--time', help='Time (in minutes) to run (-1 denotes run forever, \
0 denotes run for one iteration).', type=IntRange(-1,), default=run_time)
parser.add_argument('-s', '--sat', help='Get info on visible satellites.', action='store_true')
parser.add_argument('-v', '--verbosity', help='Verbosity level 0 (silent) to 3 (most verbose).',
                    type=IntRange(V_NONE, V_HIGH), default=V_HIGH)
parser.add_argument('-p', '--port',
                    default=PORT_DEFAULT,
                    dest='port',
                    type=IntRange(PORT_LOW, PORT_HIGH),
                    help='Port number used to connect to remote server')
parser.add_argument('-d', '--direct', help='Connect direct to gpsd daemon instead of through server. \n\n'
                          f'**NOTE** -p(ort) argument is ignored in this case as gpsd daemon uses port {GPSD_PORT}',
                    action='store_true')

# Read arguments passed on command line
args = parser.parse_args()
port = args.port
fname = ''  # filename to log to
# create logging methods based on verbosity level
log = AspLogger(args.verbosity)

# Parse command line arguments
server_addr = args.serverIP  # Server IP  - not optional

if not (valid_ip(server_addr)):
    log.erro(f'IP address {server_addr} invalid. Exiting.')
    exit(-1)
if args.log is not None:  # Log filename - optional
    fname = args.log
    # Check for valid filename?
    logging = True
if args.freq is not None:  # Read frequency (seconds) - optional (default defined above)
    archive_freq = args.freq
if args.time is not None:  # Run duration (minutes) - optional (default defined above)
    run_time = args.time
if args.direct:
    from gps import *

if logging:
    # Open the file and write the header
    f = open(fname, 'a')
    if args.sat:
        f.write('Date Sat #,Azimuth,Elevation (deg),Signal (s/n)\n')
    else:
        f.write('Date Time,Lat,Lon\n')

# Write initial parameters to console
log.info('Acquisition started with following parameters:')
if logging:
    log.info(f'     Saving to file     : {fname}')
log.info(f'     Server IP#         : {server_addr}({port})')
log.info(f'     Logging frequency  : {archive_freq} seconds')
if run_time == -1:
    log.info('     Acquiring data until stopped via user interrupt (ctrl-c)')
elif run_time == 0:
    log.info('     Acquiring data for one iteration')
else:
    log.info(f'     Acquiring data for : {run_time} minutes')
log.info('')
# Set up socket for messages
if args.direct is not True: # This is a server connection
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    retry_connect(logobj=log, sock=s, saddr=server_addr, sport=port)

# Main Loop
while True:
    if args.sat:
        try:
            if args.direct:     # Requesting satellite data direct from gps daemon
                gpsd = gps(host=server_addr, port=GPSD_PORT, mode=WATCH_ENABLE | WATCH_NEWSTYLE)
                while True:
                    nx = gpsd.next()  # Loop through messages for TPV
                    if nx['class'] == 'SKY':  # Wait for the proper message to roll around
                        gps_time = getattr(nx, 'time', "")
                        sat_dict = getattr(nx, 'satellites', "")
                        num_sat = len(sat_dict)
                        satellites = list()
                        for sat in sat_dict:
                            satellites.append(f'{sat.PRN},{sat.az},{sat.el},{sat.ss}')
                        gpsd.close()
                        break

            else:   # Requesting data from gps server
                s.sendall(MSG_READ_SAT)
                tdata = s.recv(1024)    # First grab GPS time from stream
                gps_time = tdata.decode("utf-8")
                data = s.recv(1024).decode()  # Retrieve the satellite records **BLOCKS**
                satellites = data.split('|')  # Create the list of satellites

            if logging:
                data_line = f'{log.timestamp()} GPS time: {gps_time}'
                f = open(fname, 'a')
                f.write(data_line + '\n')
                f.close()

            # Do not log any time info for single-iteration run (run_time = 0)
            if run_time < 0:
                log.info(f'Run time:  {accum_time} seconds')
            elif run_time > 0:
                log.info(f'Run time: {accum_time} of {int(run_time) * 60} seconds')

            log.info(f'Found {len(satellites)} visible satellites')
            gdate = gps_time.split('T')[0]
            gtime = gps_time.split('T')[1].split('.')[0]
            log.info(f'GPS date: {gdate}')
            log.info(f'GPS time: {gtime}Z')
            for satellite in satellites:
                elem = satellite.split(',')  # type : List[str]
                # data in format : Sat #, azimuth, elevation, s/n ratio
                s_num = elem[0]
                s_az = elem[1]
                s_el = elem[2]
                s_ss = elem[3]
                if logging:
                    data_line = f'{log.timestamp()} {elem[0]},{elem[1]},{elem[2]},{elem[3]}'
                    f = open(fname, 'a')
                    f.write(data_line + '\n')
                    f.close()
                log.info(f'Sat #{s_num:0>3}: {s_az:0>3}\N{DEGREE SIGN}az, {s_el:0>2}\N{DEGREE SIGN}el,'
                         f' s/n({s_ss:0>2})')
            log.info('')

            if (run_time > 0) and (accum_time >= int(run_time) * 60) or run_time == 0:
                log.info('Acquisition complete.')
                s.sendall(MSG_DISCONNECT)
                s.close()
                exit(0)
            time.sleep(archive_freq)
            accum_time += archive_freq

        except ConnectionError as exc:
            log.warn(f'Problem connecting to server: {exc}')
            s.close()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            retry_connect(logobj=log, sock=s, saddr=server_addr, sport=port)

        except socket.timeout:
            log.warn('Timeout waiting for server response.')

        except IndexError:
            log.warn(f'Malformed message from server : {data.decode("utf-8")}')

        except KeyboardInterrupt:
            if logging:
                f.close()
            if run_time <= 0:
                log.info('Program terminated via user interrupt.')
                exit(0)
            else:
                log.warn('Unexpected program termination via user interrupt.')
                exit(-1)

    else:   # Must be a READ_POS request
        try:
            if args.direct:     # Direct connection to gpsd
                gpsd = gps(host=server_addr, port=GPSD_PORT, mode=WATCH_ENABLE | WATCH_NEWSTYLE)
                while True:
                    nx = gpsd.next()  # Loop through messages for TPV
                    if nx['class'] == 'TPV':
                        lat = getattr(nx, 'lat', "Unknown")
                        lon = getattr(nx, 'lon', "Unknown")
                        gtm = getattr(nx, 'time', "Unknown")
                        data = f'{lat},{lon}'
                        break
                gpsd.close()    # Must close daemon connection to flush buffer
            else:   # Connecting to gps server
                s.sendall(MSG_READ_POS)
                data = s.recv(1024).decode("utf-8")
                elem = data.split(',')  # type : List[str]
                gtm = elem[0]
                lat = elem[1]
                lon = elem[2]

            if logging:
                data_line = f'{log.timestamp()},{data}'
                f = open(fname, 'a')
                f.write(data_line + '\n')
                f.close()
            if run_time < 0:
                log.info(f'Run time:  {accum_time} seconds')
            else:
                log.info(f'Run time: {accum_time} of {int(run_time) * 60} seconds')
            log.info(f'GPS time: {gtm}')
            log.info(f'GPS position: {lat},{lon}')
            log.info('')

            if (run_time > 0) and (accum_time >= int(run_time) * 60) or run_time == 0:
                log.info('Acquisition complete.')
                s.sendall(MSG_DISCONNECT)
                s.close()
                exit(0)
            time.sleep(archive_freq)
            accum_time += archive_freq

        except ConnectionError as exc:
            log.warn(f'Problem connecting to server: {exc}')
            s.close()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            retry_connect(logobj=log, sock=s, saddr=server_addr, sport=port)

        except socket.timeout:
            log.warn('Timeout waiting for server response.')

        except IndexError:
            log.warn(f'Malformed message from server : {data.decode("utf-8")}')

        except KeyboardInterrupt:
            if logging:
                f.close()
            if run_time <= 0:
                log.info('Program terminated via user interrupt.')
                exit(0)
            else:
                log.warn('Unexpected program termination via user interrupt.')
                exit(-1)
