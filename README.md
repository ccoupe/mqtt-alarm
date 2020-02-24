## Hubitat Alarm
Hubitat Alarm is "device" on Linux and/or OSX that plays a TTS mp3 from
Hubitat. It provides these capabilities: notification, speak and siren(in v2).

It makes the computer attached speakers available for hubitat to use for
notications and speaking. It is not a media player in Hubitat or HomeAssistant terminolgy.
Note that the 'sound' is mixed into what ever is playing. This is not ideal but
pausing all the media players that the user might be running is a formidable task
(if it could be done - it would be 'muy pesky').

It requires an MQTT server on the network, a hubitat driver MQTT-Alarm,  and
one of the linux or osx 'devices' provided here. The 'device' listens for an
mqtt message (the url of an mp3 on the Hubitat hub) and plays it on the
computers speakers. Simple, if it weren't for those pesky details.

From the linux or osx perspective the 'device' is a background program, a daemon
that loads at system startup time. This not the same as User login time, so the
'device' is available for a logged out (but running) system.  That means many things 
in how it's implemented - it runs as root, it uses systemd on Linux and launchd on OSX
the network must be running when the app is started at boot time. 

There are also MQTT details and protocols to deal with and it's not a simple
installation.  You need python3 which may not be the default or installed on
OSX or Linux. That means you need to install it (Homebrew on OSX and possibly Xcode) and that
is beyond these instructions. You have to edit lots of little files so there is
plenty of opportunity for typos and misunderstandings. And you'll have to reboot to 
test that it does load at boot. 

You also need a MQTT server somewhere on your network. I use mosquitto running
on a Raspberry Pi. The MQTT topics are supposed to be Homie v3 compatible. 

## Install 
### Prepare Local system(s)
Find a place to store the files. I use ~/.hubitat/alarm but /usr/local/share/hubitat/alarm
might be a better place.  Also be aware that it's really and MQTT device, not a hubitat
only device. Somethings the names of things don't match that concept. Maybe
/usr/local/share/mqtt/alarm would be best? We're going to be sudo'd most of the time
```sh
sudo -s
mkdir -p /usr/local/share/hubitat/alarm
cd  /usr/local/share/hubitat
git clone https://github.com/ccoupe/mqtt-alarm.git
cd mqtt-alarm/alarm
```
Notice that everything belongs to root. Not ideal but we live with it.

Do a `which python3` . Remember that location. Also remember the ip address 
of your MQTT server. Mine is 192.168.1.7 so that's what you'll see down below.
Now modify mqtt-alarm.sh (Linux) or iot-alarm.sh (OSX). You want the full path for
python3 and the full path to the install directory. You can not use relative paths.

We need a file that describes the device to MQTT. I have bronco.json and mini.json
because those are the names of my Linux and Mac machines. Could be any name you like.
The field values should be changed for your situation. Always create unique mqtt_client_names.
It doesn't matter what they are as long as MQTT thinks they are unique. The `homie_device`
will be used when you install the groovy driver. Your alarm is a device it may have many 
sub-devices or properties but it's a device to Hubitat and MQTT/Homie. The `homie_name` is just a 
user friendly descriptive name. It's required by Homie but we don't use it. We do require it.
#### bronco.json
{
  "mqtt_server_ip": "192.168.1.7",
  "mqtt_port": 1883,
  "mqtt_client_name": "bronco_play1",
  "homie_device": "bronco_play",
  "homie_name": "Bronco Mp3 Play"
}
#### mini.json
{
  "mqtt_server_ip": "192.168.1.7",
  "mqtt_port": 1883,
  "mqtt_client_name": "mini_play1",
  "homie_device": "mini_play",
  "homie_name": "Mac mini Mp3 Play"
}
#### mqtt-alarm.sh 
```sh
#/bin/bash
cd /home/ccoupe/.hubitat/alarm
/usr/bin/python3 alarm.py -d2 -c bronco.json
```
#### iot-alarm.sh
```sh 
#/bin/bash
cd /Users/ccoupe/.hubitat/alarm
sleep 60
/usr/sbin/ipconfig waitall
echo "Network up?"
/usr/local/bin/python3 alarm.py -d3 -c mini.json
```
#### Load the daemon
There is no way around this. It's likely there is a mistake, somewhere. Finding
the damn log files and figuring out what is wrong is not easy. 
##### systemd
On Linux we copy the `hubitatalarm.service` file where systemd can find it. Then
we tell systemd to enable it and to run it. First we need that file
```
[Unit]
Description=MQTT Alarm
After=network-online.target

[Service]
ExecStart=/home/ccoupe/.hubitat/alarm/mqtt-alarm.sh
Restart=on-abort

[Install]
WantedBy=multi-user.target
```
Of cource you want to use the full path to where the script lives. So edit
the file. Now copy to where systemd can find it.
```
sudo cp hubitatalarm.service /etc/systemd/system
sudo systemctl enable hubitatalarm
sudo systemctl start hubitatalarm
```
See if it is running. `ps ax | grep hubitat`. or journalctl,
##### launchctl
#### Hubitat Driver
Install the groovy driver. 
### Test
test.
reboot, test again
### V2
Version 2, should it appear, could allow for siren and chime sounds. These
mp3 files would have to located and installed by the user and entries made in
the json file. 
### Additional thoughts
Yes, you could have one 'alarm' device in Hubitat and MQTT and bronco.json
and mini.json could specify the same device name and topic. There are few good
reasons to do that. Just make sure the client names are unique. 
