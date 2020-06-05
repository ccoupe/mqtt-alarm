#!/bin/bash
cd /usr/local/share/hubitat/mqttalarm
sleep 60
/usr/sbin/ipconfig waitall
echo "Network up?"
/usr/local/bin/python3 alarm.py -d3 -c mini.json
