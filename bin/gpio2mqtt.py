#!/usr/bin/env python3
############################################################
## Description
## GPIO-MQTT gateway
##
## prerequisites:
##          python, PIP
##			pip install rpi.gpio
## 			pip install paho-mqtt

from MqttClient import MqttClient
from Channel import Channel

from datetime import datetime
import RPi.GPIO as GPIO
import logging

import getopt
import sys

# ======================
##
# Mapping Loglevel from loxberry log to python logging
##

def map_loglevel(loxlevel):
    switcher={
        0:logging.NOTSET,
        3:logging.ERROR,
        4:logging.WARNING,
        6:logging.INFO,
        7:logging.DEBUG
    }
    return switcher.get(int(loxlevel),"unsupported loglevel")

# ======================
##
# handle start arguments
##
inputs = None
outputs = None
loglevel=logging.ERROR
logfile=""
logfileArg = ""
lbhomedir = ""
configfile = ""
opts, args = getopt.getopt(sys.argv[1:], 'f:l:c:h:', ['logfile=', 'loglevel=', 'configfile=', 'lbhomedir='])
for opt, arg in opts:
    if opt in ('-f', '--logfile'):
        logfile=arg
        logfileArg = arg
    elif opt in ('-l', '--loglevel'):
        loglevel=map_loglevel(arg)
    elif opt in ('-c', '--configfile'):
        configfile=arg
    elif opt in ('-h', '--lbhomedir'):
        lbhomedir=arg

# ==============
##
# Setup logger function
##
def setup_logger(name):

    global loglevel
    global logfile

    logging.captureWarnings(1)
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()

    logger.addHandler(handler)
    logger.setLevel(loglevel)

    if not logfile:
        logfile="/tmp/"+datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]+"_gpio2mqtt.log"
    logging.basicConfig(filename=logfile,level=loglevel,format='%(asctime)s.%(msecs)03d <%(levelname)s> %(message)s',datefmt='%H:%M:%S')

    return logger

_LOGGER = setup_logger("GPIO2MQTT")
_LOGGER.debug("logfile: " + logfileArg)
_LOGGER.info("loglevel: " + logging.getLevelName(_LOGGER.level))

# ============================
# init MQTT
# ============================
client = MqttClient(lbhomedir + '/data/system/plugindatabase.json', _LOGGER)

# ============================
##
# setup GPIOS
##
Channel.init(configfile, _LOGGER, client)

Channel.sendChannelStates()
# ============================
##
# start mqtt Client
##
try:
    _LOGGER.info("start MQTT Client")

    client.loop_forever()
except Exception as e:
    _LOGGER.exception(str(e))
# except KeyboardInterrupt:
#     _LOGGER.info("Stop MQTT Client")
#     client.disconnect() # disconnect gracefully
#     client.loop_stop() # stops network loop
#     GPIO.cleanup()
#     logging.shutdown()
finally:
    _LOGGER.info("Stop MQTT Client")
    client.disconnect() # disconnect gracefully
    GPIO.cleanup()
    logging.shutdown()
# ============================
