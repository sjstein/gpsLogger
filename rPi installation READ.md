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

However, I was able to abbreviate the installation process a bit (not grabbing a tarbal) by cloning and building:

`# git clone https://gitlab.com/gpsd/gpsd.git`
`# cd gpsd`
`# scons --config=force && scons install`
