## Hubitat MQTT Alarm
MQTT Alarm is "device" on Linux and/or OSX that plays a TTS mp3 from
Hubitat. It provides these capabilities: notification, speak.

It makes the computer attached speakers available for Hubitat to use for
notifications and speaking. It is not a media player in Hubitat or HomeAssistant terminolgy.
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
sudo -sH
mkdir -p /usr/local/share/hubitat/alarm
cd  /usr/local/share/hubitat
git clone https://github.com/ccoupe/mqtt-alarm.git
cd mqtt-alarm
```
Notice that everything belongs to root. Not ideal but we live with it. Tha

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
#### python dependencies
```sh
pip3 install paho-mqtt
pip3 install playsound
```
Caution: You may have several python3 library locations. We want a python3
that is available at boot time. The '-H' flag on sudo may be required. 
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
#!/bin/bash
cd /usr/local/share/hubitat/mqtt-alarm
/usr/bin/python3 alarm.py -d2 -c bronco.json
```
#### iot-alarm.sh
```sh 
#!/bin/bash
cd /usr/local/share/hubitat/mqtt-alarm
sleep 60
/usr/sbin/ipconfig waitall
echo "Network up?"
/usr/local/bin/python3 alarm.py -d2 -c mini.json
```
#### Quick Test
we want to test our typing skills. `cd ../` and then 
`./mqtt-alarm/mqtt-alarm.sh` or `./mqtt-alarm/iot-alarm.sh`
you'll get some startup info and ending with `Subscribing:  0` and it waits
for the MQTT server to send something. Control-C. It's working well enough
for now. If you have MQTT-Explorer installed and you should, then you can look
at the MQTT structure you just created. 

We know it runs. Now we want to load at boot time. Go back into the directory
`cd mqtt-alarm`

#### Load the daemon
There is no way around this. It's likely there are mistake, somewhere. Finding
the damn log files and figuring out what is wrong is not easy. 

##### Linux systemd
On Linux we copy the `hubitat-alarm.service` file where systemd can find it. Then
we tell systemd to enable it and to run it. First we need that file hubitat-alarm.service:
```
[Unit]
Description=MQTT Alarm
After=network-online.target

[Service]
ExecStart=/usr/local/share/hubitat/mqtt-alarm/mqtt-alarm.sh
Restart=on-abort

[Install]
WantedBy=multi-user.target
```
Of cource you want to use the full path to where the script lives. So edit
the file. Now copy to where systemd can find it.
```
cp hubitat-alarm.service /etc/systemd/system
systemctl enable hubitat-alarm
systemctl start hubitat-alarm
```
See if it is running: `ps ax | grep hubitat`. Or use journalctl to look
at the log or /var/log/syslog. You should reboot and insure that the alarm
code is running.

##### OSX launchctl
OSX can be really picky about startup. On the bright side, /usr/local/share
isn't owned by root or wheel.  We use an iot-alarm.plist:
```sh
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
   <key>Label</key>
   <string>com.mvmanila.iot-alarm</string>
   <key>ProgramArguments</key>
   <array>
         <string>/usr/local/share/hubitat/mqtt-alarm/iot-alarm.sh</string>
   </array>
   <key>StandardOutPath</key>
   <string>/var/log/iot-alarm.log</string>
   <key>StandardErrorPath</key>
   <string>/var/log/iot-alarm.log</string>
   <key>KeepAlive</key>
   <dict>
        <key>NetworkState</key>
        <true/>
   </dict>
   <key>RunAtLoad</key>
   <true/>
</dict>
</plist>
```
That should wait for the network to be up and running before attempting
to run the script. Should, but doesn't. Notice the 60 second delay in the
launch script iot-alarm.sh ? Now you know why it's there.

```sh
sudo cp iot-alarm.plist /Library/LaunchDaemons/
sudo launchctl load iot-alarm.plist
```
Do `ps ax | grep alarm` to see if the alarm code is running. If it isn't
you'll have to correct paths and or permissions. Make sure you are sudo root

Reboot and make sure it is running after that. Remember that one minute
timer it might still be waiting. You'll see two lines from the ps|grep
```sh
   78   ??  Ss     0:00.01 /bin/bash /usr/local/share/hubitat/mqtt-alarm/iot-alarm.sh
  692   ??  S      0:00.14 /usr/local/Cellar/python/3.7.5/Frameworks/Python.framework/Versions/3.7/Resources/Python.app/Contents/MacOS/Python alarm.py -d2 -c mini.json
```
#### Hubitat Driver

Download/Copy the [driver source from ](https://raw.githubusercontent.com/ccoupe/hubitat/master/mqtt-alarm.groovy)
In Hubitat, in the Drivers page, add a new divers. Paster the code and save.

Select the devices link and create a new device. Select MQTT-Alarm from way down at the end
in the user drivers selection. Give the device a name. Save. You'll get a page to setup the driver.

It's a good idea to put the Hubitat Log in another tab. 

In the Prefererences section you need to specifiy the MQTT server IP address. In the Topic to Publish
enter  "homie/homie_device" where homie_device is the name from your json file. 

Select the voice you want in the dropdown list. Save preferences. In the log you should see
a Connected message. 

### Test and Usage

In the Speak button, enter a phrase and press the button. You should hear the phrase spoken.
In the Device Notification button, you can also enter a phrase and press the button. The phrase will have some 
extra emphasis added compared to speak() The device should be usable bu Hubitat where ever such devices are usable.

Remember - you're playing a YouTube video when the speech arrives It will mix in. It is
impossible / impractical to do a pause. 
### V2
Version 2, should it appear, could allow for siren and chime sounds. These
mp3 files would have to be located and installed by the user and entries made in
the json file. 

### Additional thoughts
Yes, you could have one 'alarm' device in Hubitat and two more more Linux/OSX 'devices'
listening on one topic. There are few good
reasons to do that. Just make sure all the MQTT client names are unique. If not unique, you'll
need to know how `ps` and `kill 9` works.
