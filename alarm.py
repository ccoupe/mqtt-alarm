#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import sys
import json
import argparse
import warnings
from datetime import datetime
import time
from threading import Thread
import socket
import os
import platform
from subprocess import Popen
from lib.Settings import Settings
from lib.Homie_MQTT import Homie_MQTT
from lib.Audio import AudioDev
import urllib.request
import logging
import logging.handlers

# NOTE: Beware the threading. Player,Chime.Siren are designed to
# be rentrant so they can be stopped. It's a feature.

# globals
settings = None
hmqtt = None
debug_level = 1
isPi = False
applog = None
audiodev = None

play_mp3 = False
player_obj = None

def mp3_player(fp):
  global player_obj, applog, audiodev
  cmd = f'{audiodev.play_mp3_cmd} {fp}'
  player_obj = Popen('exec ' + cmd, shell=True)
  player_obj.wait()

# Restore volume if it was changed
def player_reset():
  global settings, applog, audiodev
  if settings.player_vol != settings.player_vol_default and not audiodev.broken:
    applog.info(f'reset player vol to {settings.player_vol_default}')
    settings.player_vol = settings.player_vol_default
    audiodev.set_volume(settings.player_vol_default)

def playUrl(url):
  global hmqtt, audiodev, applog, settings, player_mp3, player_obj
  applog.info(f'playUrl: {url}')
  if url == 'off':
    if player_mp3 != True:
      return
    player_mp3 = False
    applog.info("killing tts")
    player_obj.terminate()
    player_reset()
    hmqtt.set_status("ready")
  else:
    try:
      urllib.request.urlretrieve(url, settings.tmpf)
    except:
      applog.warn(f"Failed download of {url}")
    hmqtt.set_status("busy")
    # change the volume?
    if settings.player_vol != settings.player_vol_default and not audiodev.broken:
      applog.info(f'set player vol to {settings.player_vol}')
      audiodev.set_volume(settings.player_vol)
    player_mp3 = True
    mp3_player(settings.tmpf)
    player_reset()
    hmqtt.set_status("ready")
    applog.info('tts finished')
  
# in order to kill a subprocess running mpg123 (in this case)
# we need a Popen object. I want the Shell too. 
playSiren = False
siren_obj = None

def siren_loop(fn):
  global playSiren, isDarwin, hmqtt, applog, siren_obj
  cmd = f'{audiodev.play_mp3_cmd} sirens/{fn}'
  while True:
    if playSiren == False:
      break
    siren_obj = Popen('exec ' + cmd, shell=True)
    siren_obj.wait()
    
# Restore volume if it was changed
def siren_reset():
  global settings, applog, audiodev
  if settings.siren_vol != settings.siren_vol_default and not audiodev.broken:
    applog.info(f'reset siren vol to {settings.siren_vol_default}')
    settings.siren_vol = settings.siren_vol_default
    audiodev.set_volume(settings.siren_vol_default)

def sirenCb(msg):
  global applog, hmqtt, playSiren, siren_obj, audiodev
  if msg == 'off':
    if playSiren == False:
      return
    playSiren = False
    hmqtt.set_status("ready")
    applog.info("killing siren")
    siren_obj.terminate()
    siren_reset()
  else:
    if settings.siren_vol != settings.siren_vol_default and not audiodev.broken:
      applog.info(f'set siren vol to {settings.siren_vol}')
      audiodev.set_volume(settings.siren_vol)
    if msg == 'on':
      fn = 'Siren.mp3'
    else:
      fn = msg
    applog.info(f'play siren: {fn}')
    hmqtt.set_status("busy")
    playSiren = True
    siren_loop(fn)
    siren_reset()
    applog.info('siren finished')
    hmqtt.set_status("ready")


play_chime = False
chime_obj = None

def chime_mp3(fp):
  global chime_obj, applog, audiodev
  cmd = f'{audiodev.play_mp3_cmd} {fp}'
  chime_obj = Popen('exec ' + cmd, shell=True)
  chime_obj.wait()

# Restore volume if it was changed
def chime_reset():
  global settings, applog, audiodev
  if settings.chime_vol != settings.chime_vol_default and not audiodev.broken:
    applog.info(f'reset chime vol to {settings.chime_vol_default}')
    settings.chime_vol = settings.chime_vol_default
    audiodev.set_volume(settings.chime_vol_default)

def chimeCb(msg):
  global applog, chime_obj, play_chime, settings, audiodev
  if msg == 'off':
    if play_chime != True:
      return
    play_chime = False
    applog.info("killing chime")
    chime_obj.terminate()
    chime_reset()
    hmqtt.set_status("ready")
  else:
    # if volume != volume_default, set new volume, temporary
    if settings.chime_vol != settings.chime_vol_default and not audiodev.broken:
      applog.info(f'set chime vol to {settings.chime_vol}')
      audiodev.set_volume(settings.chime_vol)
    flds = msg.split('-')
    num = int(flds[0].strip())
    nm = flds[1].strip()
    fn = 'chimes/' + nm + '.mp3'
    applog.info(f'play chime: {fn}')
    hmqtt.set_status("busy")
    play_chime = True
    chime_mp3(fn)
    chime_reset()
    hmqtt.set_status("ready")
    applog.info('chime finished')

# TODO: order Lasers with rotating/pan motors. ;-)       
def strobeCb(msg):
  global applog, isPi, hmqtt
  applog.info(f'missing lasers for strobe {msg} Cheapskate!')

def log(msg, level=2):
  global debug_level
  if level > debug_level:
    return
  (dt, micro) = datetime.now().strftime('%H:%M:%S.%f').split('.')
  dt = "%s.%03d" % (dt, int(micro) / 1000)
  logmsg = "%-14.14s%-60.60s" % (dt, msg)
  print(logmsg, flush=True)
 
def main():
  global isDarwin, settings, hmqtt, applog, audiodev
  # process cmdline arguments
  loglevels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
  ap = argparse.ArgumentParser()
  ap.add_argument("-c", "--conf", required=True, type=str,
    help="path and name of the json configuration file")
  ap.add_argument("-s", "--syslog", action = 'store_true',
    default=False, help="use syslog")
  ap.add_argument("-d", "--debug", action='store', type=int, default='3',
    nargs='?', help="debug level, default is 3")
  args = vars(ap.parse_args())
  
  # logging setup
  applog = logging.getLogger('mqttplayer')
  #applog.setLevel(args['log'])
  if args['syslog']:
    applog.setLevel(logging.DEBUG)
    handler = logging.handlers.SysLogHandler(address = '/dev/log')
    # formatter for syslog (no date/time or appname. Just  msg.
    formatter = logging.Formatter('%(name)s-%(levelname)-5s: %(message)-40s')
    handler.setFormatter(formatter)
    applog.addHandler(handler)
  else:
    logging.basicConfig(level=logging.DEBUG,datefmt="%H:%M:%S",format='%(asctime)s %(levelname)-5s %(message)-40s')

  
  
  audiodev = AudioDev()
  isDarwin = audiodev.isDarwin
  settings = Settings(args["conf"], 
                      audiodev,
                      applog)
  
  hmqtt = Homie_MQTT(settings, 
                    playUrl,
                    chimeCb,
                    sirenCb,
                    strobeCb)
  settings.print()
  
  # fix debug levels
  if args['debug'] == None:
    debug_level = 3
  else:
    debug_level = args['debug']
    
  # All we do now is loop over a 5 minute delay
  while True:
    time.sleep(5*60)
  
if __name__ == '__main__':
  sys.exit(main())
