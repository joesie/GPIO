#!/usr/bin/env python3
############################################################
## Description
## GPIO-MQTT gateway
##
## prerequisites:
##          python, PIP
##			pip install rpi.gpio
## 			pip install paho-mqtt

from bin.MqttClient import MqttClient
from Channel import Channel, OutputChannel
import paho.mqtt.client as mqtt
import time
import threading
from datetime import datetime
import RPi.GPIO as GPIO
import json
import logging

import getopt
import sys
import socket

SleepTimeL = 0.2

#Configuration MQTT Topics
hostname = socket.gethostname()
MQTT_TOPIC_OUTPUT  = hostname + "/gpio/set/"
MQTT_RESPONSE_STATE = hostname + "/gpio/"



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



client = MqttClient(lbhomedir + '/data/system/plugindatabase.json', _LOGGER)


# ============================
##
# get configuration from mqtt broker and store config in mqttconf variable
##
# mqttconf = None;
# try:
#     with open(lbhomedir + '/data/system/plugindatabase.json') as json_plugindatabase_file:
#         plugindatabase = json.load(json_plugindatabase_file)
#         mqttconfigdir = plugindatabase['plugins']['07a6053111afa90479675dbcd29d54b5']['directories']['lbpconfigdir']

#         mqttPluginconfig = None
#         with open(mqttconfigdir + '/mqtt.json') as json_mqttconfig_file:
#             mqttPluginconfig = json.load(json_mqttconfig_file)

#         mqttcred = None
#         with open(mqttconfigdir + '/cred.json') as json_mqttcred_file:
#             mqttcred = json.load(json_mqttcred_file)

#         mqttuser = mqttcred['Credentials']['brokeruser']
#         mqttpass = mqttcred['Credentials']['brokerpass']
#         mqttaddressArray = mqttPluginconfig['Main']['brokeraddress'].split(":")
#         mqttPort = MQTT_DEFAULT_PORT
#         if len(mqttaddressArray) > 1:
#             mqttPort = int(mqttaddressArray[1])

#         mqttconf = {
#             'username':mqttuser,
#             'password':mqttpass,
#             'address': mqttaddressArray[0],
#             'port': mqttPort
#         }
#     _LOGGER.debug("MQTT config" + str(mqttconf))
# except Exception as e:
#     _LOGGER.exception(str(e))

# If no mqtt config found leave the script with log entry
if mqttconf is None:
    _LOGGER.critical("No MQTT config found. Daemon stop working")
    sys.exit(-1)


# ============================
##
# MQTT Heartbeat
#
# def mqtt_heatbeat(name):
#     while(1):
#         client.publish(MQTT_RESPONSE_STATE+'status', "Online", retain = True)
#         time.sleep(10)


# ============================
##
# setup GPIOS
##
Channel.init(configfile, _LOGGER, client)

# ============================
##
# definition of mqtt callbacks
##
# def on_connect(client, userdata, flags, rc):
#     client.subscribe(MQTT_TOPIC_OUTPUT + "#")

# ============================
# def on_message(client, userdata, msg):
#     mymsg = str(msg.payload.decode("utf-8"))
#     mytopic = str(msg.topic)
#     _LOGGER.debug("Topic: " + mytopic + " with Payload: " + mymsg + "!")

#     if(mytopic.startswith(MQTT_TOPIC_OUTPUT + "json")):
#         if(not mymsg):
#             client.publish(MQTT_RESPONSE_STATE + "error" + "/stateText", "Error, can't set GPIO. For more information read the logfile!", retain = True)
#             _LOGGER.error('If you use json to set outputs, you have to transmit a json like {"5":"off","6":"on"}. For more information read the manual!')
#             return
#         try:
#             msg_json = json.loads(mymsg)
#             for key in msg_json:
#                 OutputChannel.handle_setOutput(key, msg_json[key])
#             return
#         except json.decoder.JSONDecodeError as ex:
#             _LOGGER.exception("Malformed json given. Cannot parse string: " + mymsg)
#         except Exception as e:
#             _LOGGER.exception(str(e))
#             client.publish(MQTT_RESPONSE_STATE + "error" + "/stateText", "Error, can't set GPIO. For more information read the logfile!", retain = True)

# 	# Search for topic in List of available output pins (BCM names) and set gpio to state LOW or HIGH
#     for i in range(0, 27):
#         if mytopic == MQTT_TOPIC_OUTPUT + str(i) :
#             try:
#                 OutputChannel.handle_setOutput(i, mymsg)
#             except Exception as e:
#                 _LOGGER.exception(str(e))
#                 client.publish(MQTT_RESPONSE_STATE + str(i) + "/stateText", "Error, can't set GPIO. For more information read the logfile!", retain = True)

# ============================
##
# start mqtt Client
##
try:
    _LOGGER.info("start MQTT Client")

    
    # client.on_connect = on_connect
    # client.on_message = on_message
    # client.username_pw_set(mqttconf['username'], mqttconf['password'])
    # client.will_set(MQTT_RESPONSE_STATE+'status', 'Offline', qos=0, retain=True)
    # client.connect(mqttconf['address'], mqttconf['port'], 60)

#     mqtt_heatbeatThread = threading.Thread(target=mqtt_heatbeat, args=(1,))
#     mqtt_heatbeatThread.start()
# #    send_state()
#     Channel.sendChannelStates()

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
    client.loop_stop() # stops network loop
    GPIO.cleanup()
    logging.shutdown()
# ============================
