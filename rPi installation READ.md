Although tempting, as of July 2020, the apt-get package for gpsd is woefully out of date, so it appears the best method to install it is to build from the repo.

I followed the guide given here: https://gpsd.gitlab.io/gpsd/installation.html
Specifically for debian:

`# apt-get update`

Multiple versions of gpsd can not co-exist on the same system. You need to ensure gpsd from a package is not on the system:

`# apt purge gpsd`

Then install the required packages:

`# apt-get install scons libncurses5-dev python-dev pps-tools`
`# apt-get install git-core`

(Note: many, if not all, of those above packages may be already installed)

At this point, the installation guide refers you to the build guide here: https://gitlab.com/gpsd/gpsd/-/blob/master/build.adoc

However, I was able to abbreviate the installation process a bit (not grabbing a tarball) by cloning and building:

`# git clone https://gitlab.com/gpsd/gpsd.git`
`# cd gpsd`
`# scons --config=force && scons install`

-----------------------------
Adding systemd configuration files

I only used the `gpsd.socket` and `gpsd.service` files. These are copied to `/etc/systemd/system/` directory.

I edited `gpsd.service` to remove the variable argument files and hard-coded them in the config:

```
[Unit]
Description=GPS (Global Positioning System) Daemon
Requires=gpsd.socket
# Needed with chrony SOCK refclock
After=chronyd.service

[Service]
Type=forking
#EnvironmentFile=-/etc/default/gpsd
#EnvironmentFile=-/etc/sysconfig/gpsd
ExecStart=/usr/local/sbin/gpsd -n -G /dev/ttyUSB0

[Install]
WantedBy=multi-user.target
Also=gpsd.socket
```

Also edit `gpsd.socket` to open up the port to remote clients:
```
[Unit]
Description=GPS (Global Positioning System) Daemon Sockets

[Socket]
ListenStream=/run/gpsd.sock
#ListenStream=[::1]:2947
#ListenStream=127.0.0.1:2947
# To allow gpsd remote access, start gpsd with the -G option and
# uncomment the next two lines:
ListenStream=[::1]:2947
ListenStream=0.0.0.0:2947
SocketMode=0600

[Install]
WantedBy=sockets.target
```

Then invoke, install and reboot:

After creating or modifying any unit files, we must tell systemd that we want it to look for new things:

`systemctl daemon-reload`

Our new service should be recognized at this point, but it won't run yet. We need to do two more things. First, tell systemd to enable it, so that it will start every time we boot:

`systemctl enable gpsd.service`

Second, start it now:

`systemctl start gpsd.service`


