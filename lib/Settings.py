#!/usr/bin/env python3
import json
import socket
from uuid import getnode as get_mac
import os 
import sys

class Settings:

  def __init__(self, etcf, adev, log):
    self.etcfname = etcf
    self.audiodev = adev
    self.log = log
    self.mqtt_server = "192.168.1.7"   # From json
    self.mqtt_port = 1883              # From json
    self.mqtt_client_name = "detection_1"   # From json
    self.homie_device = None            # From json
    self.homie_name = None              # From json
    self.tmpf = None                    # From json
    # IP and MacAddr are not important (should not be important).
    if sys.platform.startswith('linux'):
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
      s.connect(('<broadcast>', 0))
      self.our_IP =  s.getsockname()[0]
      # from stackoverflow (of course):
      self.macAddr = ':'.join(("%012x" % get_mac())[i:i+2] for i in range(0, 12, 2))
    elif sys.platform.startswith('darwin'):
      #host_name = socket.gethostname() 
      #self.our_IP = socket.gethostbyname(host_name) 
      
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.connect(("8.8.8.8", 80))
			self.our_IP = s.getsockname()[0]

      self.macAddr = ':'.join(("%012x" % get_mac())[i:i+2] for i in range(0, 12, 2))
    else:
      self.our_IP = "192.168.1.255"
      self.macAddr = "de:ad:be:ef"
    self.macAddr = self.macAddr.upper()
    self.load_settings(self.etcfname)
    self.log.info("Settings from %s" % self.etcfname)
    self.player_vol_default = self.audiodev.sink_volume
    self.chime_vol_default = self.audiodev.sink_volume
    self.siren_vol_default = self.audiodev.sink_volume
    self.player_vol = self.audiodev.sink_volume
    self.chime_vol = self.audiodev.sink_volume
    self.siren_vol = self.audiodev.sink_volume

    
  def load_settings(self, fn):
    conf = json.load(open(fn))
    if conf["mqtt_server_ip"]:
      self.mqtt_server = conf["mqtt_server_ip"]
    if conf["mqtt_port"]:
      self.mqtt_port = conf["mqtt_port"]
    if conf["mqtt_client_name"]:
      self.mqtt_client_name = conf["mqtt_client_name"]
    # v3 - Homie, 
    if conf['homie_device']:
      self.homie_device = conf['homie_device']
    if conf['homie_name']:
      self.homie_name = conf['homie_name']
    self.tmpf = conf.get('tmpf', '/tmp/hubitat_tts.mp3')


  def print(self):
    self.log.info("==== Settings ====")
    self.log.info(self.settings_serialize())
  
  def settings_serialize(self):
    st = {}
    st['mqtt_server_ip'] = self.mqtt_server
    st['mqtt_port'] = self.mqtt_port
    st['mqtt_client_name'] = self.mqtt_client_name
    st['homie_device'] = self.homie_device 
    st['homie_name'] = self.homie_name
    str = json.dumps(st)
    return str

  def settings_deserialize(self, jsonstr):
    st = json.loads(jsonstr)
