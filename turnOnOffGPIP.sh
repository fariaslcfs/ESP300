#!/usr/bin/bash

## Script to turn off and then turn on the
## GPIP adapter connected to USB port ##

## sudo uhubctl lists the usb devices ##
## Example:
# farias@EFO-Farias-Ub:~/ESP300$ sudo uhubctl
# Current status for hub 2-1 [8087:0024]
#  Port 1: 0100 power
#  Port 2: 0100 power
#  Port 3: 0100 power
#  Port 4: 0100 power
#  Port 5: 0100 power
#  Port 6: 0100 power
#  Port 7: 0100 power
#  Port 8: 0100 power
# Current status for hub 1-1 [8087:0024]
#  Port 1: 0303 power lowspeed enable connect [0000:3825  USB OPTICAL MOUSE]
#  Port 2: 0303 power lowspeed enable connect [c0f4:04c0 SZH usb keyboard]
#  Port 3: 0503 power highspeed enable connect [0957:0718 Agilent Technologies, Inc. 82357B () MY48100800]
#  Port 4: 0103 power enable connect [067b:2303 Prolific Technology Inc. USB-Serial Controller D]
#  Port 5: 0100 power
#  Port 6: 0100 power

sudo uhubctl -l 1-1 -p 3 -a off
sleep 5
sudo uhubctl -l 1-1 -p 3 -a on
