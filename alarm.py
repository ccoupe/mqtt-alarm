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
import urllib.request
from playsound import playsound
import logging
import logging.handlers


# globals
settings = None
hmqtt = None
debug_level = 1
isPi = False
applog = None
'''
def playUrl(url):
  global hmqtt, isPi, applog
  #log(url)
  applog.info("playUrl: %s" % url)
  if True:
    try:
      urllib.request.urlretrieve(url, "tmp.mp3")
    except:
      applog.warn("Failed download")
    url = "tmp.mp3"
  #synchronous playback.
  hmqtt.set_status("busy")
  hmqtt.client.loop()
  if isPi:
    os.system('mpg123 -q --no-control tmp.mp3')
  else:
    playsound(url)
  hmqtt.set_status("ready")
  hmqtt.client.loop()


def playChime(msg):
  global hmqtt, isPi, applog
  hmqtt.set_status("busy")
  hmqtt.client.loop()
  if msg != 'stop':
    # parse name out of msg ex: '11 - Enjoy'
    flds = msg.split('-')
    num = int(flds[0].strip())
    nm = flds[1].strip()
    ext = '.wav'
    if num >= 10: ext = '.mp3'
    applog.info(f'asked for {msg} => chimes/{nm}{ext}')
    if isPi:
      if ext == '.wav':
        os.system(f'aplay chimes/{nm}{ext}')
      else:
        os.system(f'mpg123 -q --no-control chimes/{nm}{ext}')
    else:
      playsound(f'chimes/{nm}{ext}')
  # stop doesn't work/do anything
  hmqtt.set_status("ready")
  hmqtt.client.loop()
'''
'''
playSiren = False
sirenThread = None
def siren_loop(fn):
  global playSiren, isPi, hmqtt, applog
  applog.debug("in thread, playing")
  while True:
    if playSiren == False:
      break
    if isPi:
      os.system(f'mpg123 -q --no-control chimes/{fn}')
    else:
      playsound(f'chimes/{fn}')

def sirenCb(msg):
  global applog, isPi, hmqtt, playSiren, sirenThread
  if msg == 'off':
    playSiren = False
    hmqtt.set_status("ready")
    applog.info("about to join")
    sirenThread.join()
  else:
    if msg == 'on':
      fn = 'Siren.mp3'
    else:
      fn = msg
    applog.info(f'play siren: {fn}')
    hmqtt.set_status("busy")
    playSiren = True
    sirenThread = Thread(target=siren_loop, args=(fn,))
    sirenThread.start()
    

play_chime = False
chime_thread = None
def chime_single(fn):
  global play_chime, isPi, hmqtt, applog
  applog.debug(f"in thread, playing {fn}")
  if isPi:
    os.system(f'mpg123 -q --no-control chimes/{fn}')
  else:
    os.system(f'mpg123 -q --no-control chimes/{fn}')
    #playsound(f'chimes/{fn}')

def chimeCb(msg):
  if msg == 'off':
    play_chime = False
    hmqtt.set_status("ready")
    applog.info("skipping join")
    #chime_thread.join()
  else:
    flds = msg.split('-')
    num = int(flds[0].strip())
    nm = flds[1].strip()
    fn = nm + '.mp3'
    applog.info(f'play chime: {fn}')
    hmqtt.set_status("busy")
    play_chime = True
    chime_thread = Thread(target=chime_single, args=(fn,))
    chime_thread.start()

  
    
# TODO: order Lasers with rotating/pan motors. ;-)       
def strobeCb(msg):
  global applog, isPi, hmqtt
  applog.info(f'missing lasers for strobe: {msg}')
'''
 

def playUrl(url):
  global hmqtt, isDarwin, applog
  applog.info("playUrl: %s" % url)
  if True:
    try:
      urllib.request.urlretrieve(url, "tmp.mp3")
    except:
      applog.warn("Failed download")
    url = "tmp.mp3"
  #synchronous playback
  hmqtt.set_status("busy")
  if isDarwin:
    os.system("afplay tmp.mp3")
  else:
    os.system('mpg123 -q --no-control tmp.mp3')
  hmqtt.set_status("ready")
  #hmqtt.client.loop()
  
# in order to kill a subprocess running mpg123 (in this case)
# we need a Popen object. I want a Shell too. 
playSiren = False
sirenThread = None
siren_obj = None

def siren_loop(fn):
  global playSiren, isDarwin, hmqtt, applog, siren_obj
  while True:
    if playSiren == False:
      break
    if isDarwin:
      cmd = f'afplay chimes/{fn}'
    else:
      cmd = f'mpg123 -q --no-control chimes/{fn}'
    siren_obj = Popen('exec ' + cmd, shell=True)
    siren_obj.wait()

def sirenCb(msg):
  global applog, isPi, hmqtt, playSiren, sirenThread, siren_obj
  if msg == 'off':
    if playSiren == False:
      return
    playSiren = False
    hmqtt.set_status("ready")
    applog.info("killing siren")
    siren_obj.terminate()
  else:
    if msg == 'on':
      fn = 'Siren.mp3'
    else:
      fn = msg
    applog.info(f'play siren: {fn}')
    hmqtt.set_status("busy")
    playSiren = True
    siren_loop(fn)
    #sirenThread = Thread(target=siren_loop, args=(fn,))
    #sirenThread.start()


play_chime = False
#chime_thread = None
chime_obj = None

def chime_mp3(fp):
  global chime_obj, applog
  if isDarwin:
    cmd = f'afplay {fp}'
  else:
    cmd = f'mpg123 -q --no-control {fp}'
  chime_obj = Popen('exec ' + cmd, shell=True)
  chime_obj.wait()

def chimeCb(msg):
  global applog, _obj, play_chime
  if msg == 'off':
    if play_chime != True:
      return
    play_chime = False
    hmqtt.set_status("ready")
    applog.info("killing chime")
    chime_obj.terminate()
  else:
    flds = msg.split('-')
    num = int(flds[0].strip())
    nm = flds[1].strip()
    fn = 'chimes/' + nm + '.mp3'
    applog.info(f'play chime: {fn}')
    hmqtt.set_status("busy")
    play_chime = True
    chime_mp3(fn)

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
  global isDarwin, settings, hmqtt, applog
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
    # formatter for syslog (no date/time or appname. Just  msg, lux, luxavg
    formatter = logging.Formatter('%(name)s-%(levelname)-5s: %(message)-30s')
    handler.setFormatter(formatter)
    #f = LuxLogFilter()
    #applog.addFilter(f)
    applog.addHandler(handler)
  else:
    logging.basicConfig(level=logging.DEBUG,datefmt="%H:%M:%S",format='%(asctime)s %(levelname)-5s %(message)-40s')
    #f = LuxLogFilter()
    #applog.addFilter(f)
  
  isDarwin = (platform.system() == 'Darwin')
  
  settings = Settings(args["conf"], 
                      None,
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
