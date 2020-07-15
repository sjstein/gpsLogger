# gpsLogger

On the rPi you will need to install a few python libraries. Follow the guide here: https://maker.pro/raspberry-pi/tutorial/how-to-use-a-gps-receiver-with-raspberry-pi-4

Note: on my raspian, the serial port was at /dev/ttyUSB0

Note: In that guide they talk about disabling the system process, but this should be modified for our use to redirect that system process to look at the proper tty port

Note: For python3, you will also have to : pip3 install gps for the gps module

For systemctl startup, modify the file /etc/default/gpsd to add the serial port to listen on. In most cases:

`DEVICES="/dev/ttyUSB0"`
