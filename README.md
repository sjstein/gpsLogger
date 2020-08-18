# gpsLogger

### Raspberry Pi notes:

You will need to install a few python libraries. Follow the guide here: https://maker.pro/raspberry-pi/tutorial/how-to-use-a-gps-receiver-with-raspberry-pi-4

**Note**: on my raspian, the serial port was at /dev/ttyUSB0

**Note**: In that guide they talk about disabling the system process, but this should be modified for our use to redirect that system process to look at the proper tty port

**Note**: For python3, you will also have to : pip3 install gps for the gps module

For systemctl startup, modify the file /etc/default/gpsd to add the serial port to listen on. In most cases:

`DEVICES="/dev/ttyUSB0"`


## For the client side, there are two models for running:

```
usage: gpsMonitor.py [-h] [-l LOG] [-f FREQ] [-t TIME] [-s] [-v VERBOSITY]
                     [-p PORT] [-d]
                     serverIP

Python script to query a remote server for GPS data data, and optionally write
that data to a text file.

positional arguments:
  serverIP              IP Number of server.

optional arguments:
  -h, --help            show this help message and exit
  -l LOG, --log LOG     File name for logging (default is NO logging).
                        (default: None)
  -f FREQ, --freq FREQ  Frequency (in seconds) to read data. (default: 5)
  -t TIME, --time TIME  Time (in minutes) to run (-1 denotes run forever, 0
                        denotes run for one iteration). (default: 60)
  -s, --sat             Get info on visible satellites. (default: False)
  -v VERBOSITY, --verbosity VERBOSITY
                        Verbosity level 0 (silent) to 3 (most verbose).
                        (default: 3)
  -p PORT, --port PORT  Port number used to connect to remote server (default:
                        5015)
  -d, --direct          Connect direct to gpsd daemon instead of through
                        server. **NOTE** -p(ort) argument is ignored in this
                        case as gpsd daemon uses port 2947 (default: False)
```

### Server mode:
Similar to other ASP client/server applications, a local server can be run on the rPi which will translate queries from clients to calls to the local gpsd daemon.
Protocols are similar to other applications. 
Disadvantages to this include adding an additional system process (gpsServer) and maintaining two pieces of software.


### Daemon mode:
As long as the gpsd daemon is running on the rPi (which it has to be for any connection to a GPS receiver), it is possible for the client-side application to query the daemon directly. Using the (-d) option to do so.
This has the advantage of not adding the server overhead to the rPi, but carries with it the cost of dealing directly with the gpsd calls.

**Note**: For running the client (gpsMonitor) in direct (-d) mode, you will need to have the gps library installed on the client machine:
`python3 -m pip install gps`

----------------------

Example output:
```
\gpsLogger>python gpsMonitor.py 192.168.1.121 -d -s -t 0
20200818 12:05:45 [INFO] Acquisition started with following parameters: {gpsMonitor.py}
20200818 12:05:45 [INFO]      Server IP#         : 192.168.1.121(5015) {gpsMonitor.py}
20200818 12:05:45 [INFO]      Logging frequency  : 5 seconds {gpsMonitor.py}
20200818 12:05:45 [INFO]      Acquiring data for one iteration {gpsMonitor.py}

20200818 12:05:46 [INFO] Found 10 visible satellites {gpsMonitor.py}
20200818 12:05:46 [INFO] GPS date: 2020-08-18 {gpsMonitor.py}
20200818 12:05:46 [INFO] GPS time: 17:05:46Z {gpsMonitor.py}
20200818 12:05:46 [INFO] Sat #012: 222.0°az, 42.0°el, s/n(28.6) {gpsMonitor.py}
20200818 12:05:46 [INFO] Sat #019: 124.5°az, 13.5°el, s/n(34.2) {gpsMonitor.py}
20200818 12:05:46 [INFO] Sat #029: 310.5°az, 30.5°el, s/n(30.2) {gpsMonitor.py}
20200818 12:05:46 [INFO] Sat #005: 184.5°az, 71.5°el, s/n(31.1) {gpsMonitor.py}
20200818 12:05:46 [INFO] Sat #002: 43.5°az, 65.0°el, s/n(26.0) {gpsMonitor.py}
20200818 12:05:46 [INFO] Sat #006: 70.5°az, 26.0°el, s/n(21.8) {gpsMonitor.py}
20200818 12:05:46 [INFO] Sat #009: 48.0°az, 15.5°el, s/n(28.1) {gpsMonitor.py}
20200818 12:05:46 [INFO] Sat #025: 270.0°az, 41.0°el, s/n(22.7) {gpsMonitor.py}
20200818 12:05:46 [INFO] Sat #013: 157.5°az, 2.5°el, s/n(17.2) {gpsMonitor.py}
20200818 12:05:46 [INFO] Sat #133: 232.5°az, 26.0°el, s/n(35.0) {gpsMonitor.py}

20200818 12:05:46 [INFO] Acquisition complete. {gpsMonitor.py}
```