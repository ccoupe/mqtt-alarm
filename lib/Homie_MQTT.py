#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import sys, traceback
import json
from datetime import datetime
from threading import Thread
import time

import time

class Homie_MQTT:

  def __init__(self, settings, playCb, chimeCb, sirenCb, strobeCb):
    self.settings = settings
    self.log = settings.log
    self.playCb = playCb
    self.chimeCb = chimeCb
    self.sirenCb = sirenCb
    self.strobeCb = strobeCb
    # init server connection
    self.client = mqtt.Client(settings.mqtt_client_name, False)
    self.client.reconnect_delay_set(min_delay=1, max_delay=60)
    #self.client.max_queued_messages_set(3)

    hdevice = self.hdevice = self.settings.homie_device  # "device_name"
    hlname = self.hlname = self.settings.homie_name     # "Display Name"
    # beware async timing with on_connect
    #self.client.on_connect = self.on_connect
    #self.client.on_subscribe = self.on_subscribe
    self.client.on_message = self.on_message
    self.client.on_disconnect = self.on_disconnect
    rc = self.client.connect(settings.mqtt_server, settings.mqtt_port)
    if rc != mqtt.MQTT_ERR_SUCCESS:
        self.log.warn("network missing?")
        exit()
    self.client.loop_start()
      
    # short cuts to stuff we really care about
    self.hurl_sub = "homie/"+hdevice+"/player/url/set"
    self.hurlvol_sub = "homie/"+hdevice+"/player/volume/set"
    self.state_pub = "homie/"+hdevice+"/$state"
    self.hchime_sub = "homie/"+hdevice+"/chime/state/set"
    self.hchimevol_sub = "homie/"+hdevice+"/chime/volume/set"
    self.hsiren_sub = "homie/"+hdevice+"/siren/state/set"
    self.hsirenvol_sub = "homie/"+hdevice+"/siren/volume/set"
    self.hstrobe_sub = "homie/"+hdevice+"/strobe/state/set"
    
    # we should publish to:
    self.hurlvol_pub = "homie/"+hdevice+"/player/volume"
    self.hchimevol_pub = "homie/"+hdevice+"/chime/volume"
    self.hsirenvol_pub = "homie/"+hdevice+"/siren/volume"

    # self.log.debug("Homie_MQTT __init__")
    self.create_topics(hdevice, hlname)
    for sub in [self.hurl_sub, self.hchime_sub, self.hsiren_sub, self.hstrobe_sub,
          self.hurlvol_sub, self.hchimevol_sub, self.hsirenvol_sub]:    
      rc,_ = self.client.subscribe(sub)
      if rc != mqtt.MQTT_ERR_SUCCESS:
        self.log.warn("Subscribe failed: %d" %rc)
      else:
        self.log.debug("Init() Subscribed to %s" % sub)
      
     
  def create_topics(self, hdevice, hlname):
    self.log.debug("Begin topic creation")
    # create topic structure at server - these are retained! 
    self.publish_structure("homie/"+hdevice+"/$homie", "3.0.1")
    self.publish_structure("homie/"+hdevice+"/$name", hlname)
    self.publish_structure(self.state_pub, "ready")
    self.publish_structure("homie/"+hdevice+"/$mac", self.settings.macAddr)
    self.publish_structure("homie/"+hdevice+"/$localip", self.settings.our_IP)
    # could have two nodes, player and alarm
    self.publish_structure("homie/"+hdevice+"/$nodes", "player,chime,siren,strobe")
    
    # player node
    self.publish_structure("homie/"+hdevice+"/player/$name", hlname)
    self.publish_structure("homie/"+hdevice+"/player/$type", "audiosink")
    self.publish_structure("homie/"+hdevice+"/player/$properties","volume,url")
    # url Property of 'play'
    self.publish_structure("homie/"+hdevice+"/player/url/$name", hlname)
    self.publish_structure("homie/"+hdevice+"/player/url/$datatype", "string")
    self.publish_structure("homie/"+hdevice+"/player/url/$settable", "false")
    self.publish_structure("homie/"+hdevice+"/player/url/$retained", "true")
    # volume Property of 'play'
    self.publish_structure("homie/"+hdevice+"/player/volume/$name", hlname)
    self.publish_structure("homie/"+hdevice+"/player/volume/$datatype", "integer")
    self.publish_structure("homie/"+hdevice+"/player/volume/$format", "0:100")
    self.publish_structure("homie/"+hdevice+"/player/volume/$settable", "false")
    self.publish_structure("homie/"+hdevice+"/player/volume/$retained", "true")

    # chime node
    self.publish_structure("homie/"+hdevice+"/chime/$name", hlname)
    self.publish_structure("homie/"+hdevice+"/chime/$type", "chime")
    self.publish_structure("homie/"+hdevice+"/chime/$properties","sound,volume")
    # state Property of 'chime'
    self.publish_structure("homie/"+hdevice+"/chime/state/$name", hlname)
    self.publish_structure("homie/"+hdevice+"/chime/state/$datatype", "string")
    self.publish_structure("homie/"+hdevice+"/chime/state/$settable", "false")
    self.publish_structure("homie/"+hdevice+"/chime/state/$retained", "true")
    # volume Property of 'chime'
    self.publish_structure("homie/"+hdevice+"/chime/volume/$name", hlname)
    self.publish_structure("homie/"+hdevice+"/chime/volume/$datatype", "integer")
    self.publish_structure("homie/"+hdevice+"/chime/volume/$format", "0:100")
    self.publish_structure("homie/"+hdevice+"/chime/volume/$settable", "false")
    self.publish_structure("homie/"+hdevice+"/chime/volume/$retained", "true")
    
    # siren node
    self.publish_structure("homie/"+hdevice+"/siren/$name", hlname)
    self.publish_structure("homie/"+hdevice+"/siren/$type", "siren")
    self.publish_structure("homie/"+hdevice+"/siren/$properties","sound,volume")
    # state Property of 'siren'
    self.publish_structure("homie/"+hdevice+"/siren/state/$name", hlname)
    self.publish_structure("homie/"+hdevice+"/siren/state/$datatype", "string")
    self.publish_structure("homie/"+hdevice+"/siren/state/$settable", "false")
    self.publish_structure("homie/"+hdevice+"/siren/state/$retained", "true")
    # volume Property of 'siren'
    self.publish_structure("homie/"+hdevice+"/siren/volume/$name", hlname)
    self.publish_structure("homie/"+hdevice+"/siren/volume/$datatype", "integer")
    self.publish_structure("homie/"+hdevice+"/siren/volume/$format", "0:100")
    self.publish_structure("homie/"+hdevice+"/siren/volume/$settable", "false")
    self.publish_structure("homie/"+hdevice+"/siren/volume/$retained", "true")
    
    # strobe node
    self.publish_structure("homie/"+hdevice+"/strobe/$name", hlname)
    self.publish_structure("homie/"+hdevice+"/strobe/$type", "strobe")
    self.publish_structure("homie/"+hdevice+"/strobe/$properties","sound")
    # state Property of 'siren'
    self.publish_structure("homie/"+hdevice+"/strobe/state/$name", hlname)
    self.publish_structure("homie/"+hdevice+"/strobe/state/$datatype", "string")
    self.publish_structure("homie/"+hdevice+"/strobe/state/$settable", "false")
    self.publish_structure("homie/"+hdevice+"/strobe/state/$retained", "true")
   # Done with structure. 

    self.log.debug("homie topics created")
    # nothing else to publish 
    
  def publish_structure(self, topic, payload):
    self.client.publish(topic, payload, qos=1, retain=True)
    
  def on_subscribe(self, client, userdata, mid, granted_qos):
    self.log.debug("Subscribed to %s" % self.hurl_sub)

  def on_message(self, client, userdata, message):
    settings = self.settings
    topic = message.topic
    payload = str(message.payload.decode("utf-8"))
    self.log.debug("on_message %s %s" % (topic, payload))
    try:
      if (topic == self.hurl_sub):
        ply_thr = Thread(target=self.playCb, args=(payload,))
        ply_thr.start()
      elif topic == self.hchime_sub:
        chime_thr = Thread(target=self.chimeCb, args=(payload,))
        chime_thr.start()
      elif topic == self.hsiren_sub:
        siren_thr = Thread(target=self.sirenCb, args=(payload,))
        siren_thr.start()
      elif topic == self.hstrobe_sub:
        strobe_thr = Thread(target=self.strobeCb, args=(payload,))
        strobe_thr.start()
      elif topic == self.hurlvol_sub:
        vol = int(payload)
        #settings.player_vol_default = settings.player_vol
        settings.player_vol = vol
        self.client.publish(self.hurlvol_pub, payload, qos=1, retain=False)
      elif topic == self.hchimevol_sub:
        vol = int(payload)
        #settings.chime_vol_default = settings.chime_vol
        settings.chime_vol = vol
        self.client.publish(self.hchimevol_pub, payload, qos=1, retain=False)
      elif topic == self.hsirenvol_sub:
        vol = int(payload)
        settings.siren_vol = vol
        self.client.publish(self.hsirenvol_pub, payload, qos=1, retain=False)
      else:
        self.log.debug(f"on_message() unknown command {topic} {payload}")
    except:
      traceback.print_exc()

    
  def isConnected(self):
    return self.mqtt_connected

  def on_connect(self, client, userdata, flags, rc):
    if rc != mqtt.MQTT_ERR_SUCCESS:
      self.log.warn("Connection failed")
      self.mqtt_connected = False
      time.sleep(60)
      self.client.reconnect()
    else:
      self.mqtt_connected = True
       
  def on_disconnect(self, client, userdata, rc):
    self.mqtt_connected = False
    if rc != 0:
      self.log.warn(f"mqtt disconnect: {rc}, attempting reconnect")
      self.client.reconnect()
      
  def set_status(self, str):
    self.client.publish(self.state_pub, str)
