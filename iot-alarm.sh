#!/bin/bash
cd /usr/local/share/hubitat/mqtt-alarm
sleep 60
/usr/sbin/ipconfig waitall
echo "Network up?"
/usr/local/bin/python3 alarm.py -d3 -c mini.json
