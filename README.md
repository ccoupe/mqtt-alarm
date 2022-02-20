## Hubitat MQTT Alarm
### What is it?
It's a Text to Speech device (TTS) so Hubitat can send text notifications
and it's spoken thru the audio speakers attached to a Linux or OSX system.

It can also be a Chime and a Siren because it can play mp3 files. Or all three.

It is not an easy install because I want it to start when the machine boots
up so it's a system wide thing and not a user thing. System things are never
easy.  

It is not a media player in Hubitat or HomeAssistant terminolgy.

Note that the 'sound' is mixed into what ever is playing. This is not ideal but
pausing all the media players that the user might be running is a formidable task
(if it could be done - it would be 'muy pesky').

It requires an MQTT broker on the network. This can be the same Linux box that
the speakers are attached to or a separate machine. I happen to have a raspberry
pi4 just to run the Mosquitto MQTT broker and drive my printer and a bunch of other
fun things. If you think about it, a siren or chime runs 24x7 so the linux or mac should
too and the MQTT broker should as well. It should have a UPS too. Right?

The 'device' listens for an
mqtt message (the url of an mp3 on the Hubitat hub, for example) and plays it on the
computers speakers.  When you or an automation on Hubitat sends a command to the mqtt broker then the 
broker notifies the 'device' it has work to do. Simple, if it weren't for those pesky details.  

MQTT may seem confusing. Once you see it you'll see it's not that confusing.
Using my system 'bronco' as an example. It is a Linux machine in my office, running 24x7
with speakers attached. Mqtt needs a parent device name. Mine is 'bronco_play'. Since
we attempt to be Homie v3 compatible, it's really 'homie/bronco_play;
In fact, there are 4 devices. 

1. `homie/bronco_play/siren`
2. `homie/bronco_play/chimes`
3. `homie/bronco_play/strobe`
4. `homie/bronco_play/player`

Strobe is not used. It's there but hubitat can't send to it but if it did, nothing happens.
Player is the tts device. ALL you need to specify is your choice for 'bronco_play' The
drivers supply the prefixes and suffices needed. Please, No spaces in your name or punctuation
beyond hyphen and underscore. 

From the linux or osx perspective the 'device' is a background program, a daemon
that loads at system startup time. This not the same as User login time, so the
'device' is available for a logged out (but running) system.  That means many things 
in how it's implemented - it runs as root, it uses systemd on Linux and launchd on OSX
the network must be running when the app is started at boot time. 

## Install 
Install means getting the code running on your Linux or OSX system and setting 
that up. 

It also means getting the groovy drivers installed in your Hubitat and
if you don't have one, install a MQTT broker.

And it means testing things and then you have make sure it can survive
a reboot of Your Linux system, hubitat or the Mqtt Broker. That is the hard
part. 

### MQTT install
I'm going to punt on this. It's not hard but there are so many other tutorials on
how to do that there is no point in my duplicating them.  I'm using Mosquitto on a machine 
I call `pi4` at 192.168.1.7 
If you know what `apt install mosquitto_clients` does then you're almost done with this 
part.

I highly recommend you get [MQTT Explorer from ](http://mqtt-explorer.com/) Pick the appimage
for Linux - not everybody can run Snaps and not everybody wants to. You can run Explorer on any
computer in your networ - it doesn't have to be Linux or a Raspberry pi. 

### Hubitat drivers.
Download/Copy the Hubitat driver you want to use 
1. [Mqtt_tts](https://raw.githubusercontent.com/ccoupe/hubitat/master/mqtt-tts.groovy)
2. [Mqtt_chime](https://raw.githubusercontent.com/ccoupe/hubitat/master/mqtt-chime.groovy)
3. [Mqtt_siren](https://raw.githubusercontent.com/ccoupe/hubitat/master/mqtt-siren.groovy)


In Hubitat, at the `<> Drivers Code` page, click the New Driver button. Paste the code and save.
Do not create a Hubitat device or configure anything else in Hubitat at this time. We
have more grunt work to do before playing with Hubitat. 

### Linux And OSX
Find a place to store the files. Because it's a 'system' creature then `/usr/local/lib/mqttalarm`
is a good place.

We're going to be sudo'd most of the time so be careful. If you don't have it
you'll need to install command line git and the mpg123 program.
```sh
sudo -sH
mkdir -p /usr/local/lib
cd  /usr/local/lib
git clone https://github.com/ccoupe/mqtt-alarm.git
cd mqtt-alarm
```
Notice that everything belongs to root. Not ideal but we can live with it. 

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
```
{
  "mqtt_server_ip": "192.168.1.7",
  "mqtt_port": 1883,
  "mqtt_client_name": "bronco_play1",
  "homie_device": "bronco_play",
  "homie_name": "Bronco Mp3 Play"
}
```
#### mini.json
```
{
  "mqtt_server_ip": "192.168.1.7",
  "mqtt_port": 1883,
  "mqtt_client_name": "mini_play1",
  "homie_device": "mini_play",
  "homie_name": "Mac mini Mp3 Play"
}
```
#### mqtt-alarm.sh 
```
#!/bin/bash
cd /usr/local/share/hubitat/mqtt-alarm
/usr/bin/python3 alarm.py -s -c bronco.json
```
#### iot-alarm.sh
```sh 
#!/bin/bash
cd /usr/local/share/hubitat/mqtt-alarm
sleep 60
/usr/sbin/ipconfig waitall
echo "Network up?"
/usr/local/bin/python3 alarm.py -s -c mini.json
```

#### Quick Test
Lets launch and make sure that python doesn't stumble out of the gate.
$ `python3 -c bronco.json`  or `./mqtt-alarm.sh`  Actually you should
do both, one after the other. Ctrl-C to quit. 

If you have MQTT-Explorer installed (you should), then you can look
at the MQTT structure you just created. 

We know it starts. Start it up again and skip down to the Hubitat
directions where you can test the device and have some fun. 
When its all working then come back here for the finale show of systemd or
launchctl fun.

#### Load the daemon
There is no way around this. It's likely there are mistakes, somewhere. Finding
the damn log files and figuring out what is wrong is not easy. 

##### Linux systemd
On Linux we copy the `mqttalarm.service` file where systemd can find it. Then
we tell systemd to enable it and to run it. First we need that file mqttalarm.service:
```
[Unit]
Description=MQTT Alarm
After=network-online.target

[Service]
ExecStart=/usr/local/lib/mqttalarm/mqtt-alarm.sh
Restart=on-abort

[Install]
WantedBy=multi-user.target
```
Of cource you want to use the full path to where the script lives. So edit
the file. Now copy to where systemd can find it.
```
cp mqttalarm.service /etc/systemd/system
systemctl enable mqttalarm
systemctl start mqttalarm
```
See if it is running: `ps ax | grep mqttalarm`. Or use journalctl to look
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
to run the script. It Should work. Notice the 60 second delay in the
launch script? We have to wait for the network to be up. This
requires secret knowledge on OSX. I don't have that knowledge so this 
script is going to wait for a minute. This is a long time If you are debugging
Just so you know.

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
### Hubitat

Lets test the TTS text to speech. From the Hubitat Devices page push the 'Add Virtual Device'
button.

Select the devices link and create a new device. Maybe Device Name = 'test tts'. Select Mqtt-tts from way down at the end
in the user drivers selection. Give the device a name. Save. You'll get a page to setup the driver.

It's a good idea to put the Hubitat Log in another tab. 

In the Prefererences section you need to specifiy the MQTT server IP address. In the Topic to Publish
enter  "homie_device" where homie_device is the name from your json file. 

![TTS-Prefs](https://user-images.githubusercontent.com/222691/110862071-40398880-827c-11eb-9484-73c262ad1f06.png)

Pick a voice and a volume. I suggest 50 for the volume. Do not go too loud until you know. 
For the first time user, you should enable logging.  Save preferences. In the log you should see a Connected message. 

![talktome](https://user-images.githubusercontent.com/222691/110863390-d7531000-827d-11eb-801b-49954bdedec0.png)

Under Speak button, enter a phrase and press the button. You should hear the phrase spoken. It can take half second
for Hubitat and Amazon to get things converted.

### Siren
You can use your system as a Siren. Just install the Mqtt-Siren.groovy driver and configure
a device in Hubitat.

In the siren folder is an Siren.mp3. It's played when
the Hubitat Mqtt-siren.groovy driver is told to play. By pressing the Siren button or the Both button.

![Siren](https://user-images.githubusercontent.com/222691/110872990-0f624f00-828e-11eb-8713-cce0fcb38edd.png)

If that looks more complicated than my simple description, well let me explain. In Hubitat, 'Sirens's have some 
common features so my Siren has to have them too - even if some features won't work. Strobe doesn't work. Nothing
dies if you do press the Strobe button. Nothing works either. The volume features do work. You probaby want you siren to
be louder than the TTS notifications or Chimes. 

Off works. You want to remember that. The siren goes until you turn it off. The siren device follows the rules and can be use just like
a 'real' one for Hubitat purposes. 

Obviously you can use your own mp3 file to replace the one in sirens/ directory. Just name it
Siren.mp3. 

### Chimes
You can play Chimes with your computer speakers. Look in the /usr/local/lib/chimes There are
canned mp3 sounds. Obviously you could replace the ones there with your choice.  But, you ask how does
hubitat know which sound to play?  It's a bit tricky and a bit hardcoded. Like Siren, the Hubitat rule for what 
a Chime can do is what we do and we do it the Hubitat way. For example the 'Beep' button - plays the default chime.
The default is chosen in the Preferences section. 

![Chimes-Pref](https://user-images.githubusercontent.com/222691/110875092-3c186580-8292-11eb-86cf-7bb26fdbedcd.png)

That shows my default is '3 - Horn' That gets mapped to the chimes/Horn.mp3 file. Makes sense? Not so fast.
You can also specify a sound number like '1' which maps to chimes/Doorbell.mp3. OK, that sort of makes sense.
Does 2 - Siren map to chimes/Siren.mp3 ? Yes.  So when your Rule Machine rule plays chime 11, Buckwheat Zydeco
sings. You got it.  10 and 11 exist because I want those tunes for other purposes. You can replace any of the 
5 sounds with your own mp3 if you keep the same names. If you want to change the names or add more then you'll have
to modify the Groovy code and the python code.  There are other schemes that could be employed but those work for
me. 

### Strobe

I do have a device that can be a strobe but building it is well out of scope for
this discussion. It involves servos, laser diodes and more raspberry pi's.  And much more
python. A bit expensive too after you buy a 3D printer.
