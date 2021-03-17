#!/usr/bin/env python3
############################################################
## Description
## GPIO-MQTT gateway
##
## prerequisites:
##          python, PIP
##			pip install rpi.gpio
## 			pip install paho-mqtt

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from time import sleep
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
MQTT_TOPIC_OUTPUT_RESPONSE  = hostname + "/gpio/"
MQTT_PATH_STATE_INPUT   = hostname + "/gpio/"
MQTT_DEFAULT_PORT = 1883
client = mqtt.Client()

# ======================
##
# handle start arguments
##
loglevel="ERROR"
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
        loglevel=arg
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
    logger.setLevel(logging.DEBUG)


    # Logging with standard LoxBerry log format
    numeric_loglevel = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_loglevel, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    if not logfile:
        logfile="/tmp/"+datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]+"_gpio2mqtt.log"
    logging.basicConfig(filename=logfile,level=numeric_loglevel,format='%(asctime)s.%(msecs)03d <%(levelname)s> %(message)s',datefmt='%H:%M:%S')

    return logger

_LOGGER = setup_logger("GPIO2MQTT")
_LOGGER.debug("logfile: " + logfileArg)
_LOGGER.debug("loglevel: " + loglevel)


# ============================
##
# get configuration from mqtt broker and store config in mqttconf variable
##
mqttconf = None;
with open(lbhomedir + '/data/system/plugindatabase.json') as json_plugindatabase_file:
    plugindatabase = json.load(json_plugindatabase_file)
    mqttconfigdir = plugindatabase['plugins']['07a6053111afa90479675dbcd29d54b5']['directories']['lbpconfigdir']

    mqttPluginconfig = None
    with open(mqttconfigdir + '/mqtt.json') as json_mqttconfig_file:
        mqttPluginconfig = json.load(json_mqttconfig_file)

    mqttcred = None
    with open(mqttconfigdir + '/cred.json') as json_mqttcred_file:
        mqttcred = json.load(json_mqttcred_file)

    mqttuser = mqttcred['Credentials']['brokeruser']
    mqttpass = mqttcred['Credentials']['brokerpass']
    mqttaddressArray = mqttPluginconfig['Main']['brokeraddress'].split(":")
    mqttPort = MQTT_DEFAULT_PORT
    if len(mqttaddressArray) > 1:
        mqttPort = x[1]

    mqttconf = {
        'username':mqttuser,
        'password':mqttpass,
        'address': mqttaddressArray[0],
        'port': mqttPort
    }

# If no mqtt config found leave the script with log entry
if mqttconf is None:
    _LOGGER.critical("No MQTT config found. Daemon stop working")
    sys.exit(-1)

# ============================
##
# MQTT Heartbeat
#
def mqtt_heatbeat(name):
    while(1):
        client.publish(MQTT_TOPIC_OUTPUT_RESPONSE+'status', "Online")
        time.sleep(10)

##
# Callback function for interrupt handling
##
def callback_input(channel):
 now = datetime.now()

 if GPIO.input(channel): # if SENSOR_PIN of channel == 1 or high
   _LOGGER.debug(now.strftime('%Y-%m-%d %H:%M:%S') + " : " + (MQTT_PATH_STATE_INPUT + str(channel) + ': ON'))
   client.publish(MQTT_PATH_STATE_INPUT + str(channel) + "/state" , "1")
   client.publish(MQTT_PATH_STATE_INPUT + str(channel) + "/stateText" , "ON")
   client.publish(MQTT_PATH_STATE_INPUT + str(channel) + "/timestamp_ON", now.strftime('%Y-%m-%d %H:%M:%S'))

   time.sleep(SleepTimeL);

 else: # if SENSOR_PIN of channel != 1 or low
   _LOGGER.debug( now.strftime('%Y-%m-%d %H:%M:%S') + " : " + (MQTT_PATH_STATE_INPUT + str(channel) + ': OFF'))
   client.publish(MQTT_PATH_STATE_INPUT + str(channel) + "/stateText", "OFF")
   client.publish(MQTT_PATH_STATE_INPUT + str(channel) + "/state", "0")
   client.publish(MQTT_PATH_STATE_INPUT + str(channel) + "/timestamp_OFF", now.strftime('%Y-%m-%d %H:%M:%S'))

   time.sleep(SleepTimeL);

# ============================
##
# setup GPIOS
##
GPIO.setmode(GPIO.BCM)
with open(configfile) as json_pcfg_file:
    pcfg = json.load(json_pcfg_file)
    gpio = pcfg['gpio']

    # configure inputs
    inputs = gpio['inputs']
    for i in range(0, int(inputs['count'])):
        key = "channel_{}".format(i)
        channel = inputs[key]

        wireing = GPIO.PUD_UP
        if channel['wiring'] == 'd':
            wireing = GPIO.PUD_DOWN

        GPIO.setup(int(channel['pin']), GPIO.IN, pull_up_down = wireing) # TODO: catch runtime errors while setting configuration
        GPIO.add_event_detect(int(channel['pin']) , GPIO.BOTH, callback=callback_input)
        _LOGGER.debug("set Pin " + channel['pin'] + " as Input")

    # configure outputs
    outputs = gpio['outputs']
    for i in range(0, int(outputs['count'])):
        key = "channel_{}".format(i)
        channel = outputs[key]

        GPIO.setup(int(channel['pin']), GPIO.OUT)
        GPIO.output(int(channel['pin']), GPIO.HIGH) #Default GPIO High is off
        _LOGGER.debug("set Pin " + channel['pin'] + " as Output")

# ============================
##
# definition of mqtt callbacks
##
def on_connect(client, userdata, flags, rc):
    client.subscribe(MQTT_TOPIC_OUTPUT + "#")

# ============================
def on_message(client, userdata, msg):
    mymsg = str(msg.payload.decode("utf-8"))
    mytopic = str(msg.topic)
    now = datetime.now()
    _LOGGER.debug("Topic: " + mytopic + " with Payload: " + mymsg + "!")

	# Search for topic in List of available output pins (BCM names) and set gpio to state LOW or HIGH
    for i in range(0, 27):
      if mytopic == MQTT_TOPIC_OUTPUT + str(i) :
        if mymsg == "ON" or mymsg == "1" or mymsg == "on" :
            try:
                GPIO.output(i, GPIO.LOW)
                time.sleep(SleepTimeL)
                client.publish(MQTT_TOPIC_OUTPUT_RESPONSE + str(i) + "/stateText", "ON")
                client.publish(MQTT_TOPIC_OUTPUT_RESPONSE + str(i) + "/state", "1")
                client.publish(MQTT_TOPIC_OUTPUT_RESPONSE + str(i) + "/timestamp_ON" , now.strftime('%Y-%m-%d %H:%M:%S'))
                _LOGGER.debug(MQTT_TOPIC_OUTPUT_RESPONSE + str(i) + "/|-- Timestamp ON:" +  now.strftime('%Y-%m-%d %H:%M:%S'))
            except Exception as e:
                _LOGGER.exception(str(e))
                client.publish(MQTT_TOPIC_OUTPUT_RESPONSE + str(i) + "/stateText", "Error, can't set GPIO. For more information read the logfile!")

        if mymsg == "OFF" or mymsg == "0" or mymsg == "off":
            try:
                GPIO.output(i, GPIO.HIGH)
                time.sleep(SleepTimeL)
                client.publish(MQTT_TOPIC_OUTPUT_RESPONSE + str(i) + "/stateText", "OFF")
                client.publish(MQTT_TOPIC_OUTPUT_RESPONSE + str(i) + "/state", "0")
                client.publish(MQTT_TOPIC_OUTPUT_RESPONSE + str(i) + "/timestamp_OFF"  , now.strftime('%Y-%m-%d %H:%M:%S'))
                _LOGGER.debug(MQTT_TOPIC_OUTPUT_RESPONSE + str(i) + "/|-- Timestamp OFF:" +  now.strftime('%Y-%m-%d %H:%M:%S'))
            except Exception as e:
                _LOGGER.exception(str(e))
                client.publish(MQTT_TOPIC_OUTPUT_RESPONSE + str(i) + "/stateText", "Error, can't set GPIO. For more information read the logfile!")

# ============================
##
# start mqtt Client
##
try:
    _LOGGER.info("start MQTT Client")

    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(mqttconf['username'], mqttconf['password'])
    client.will_set(MQTT_TOPIC_OUTPUT_RESPONSE+'status', 'Offline', qos=0, retain=True)
    client.connect(mqttconf['address'], mqttconf['port'], 60)

    mqtt_heatbeatThread = threading.Thread(target=mqtt_heatbeat, args=(1,))
    mqtt_heatbeatThread.start();

    client.loop_forever()
except KeyboardInterrupt:
    _LOGGER.info("Stop MQTT Client")
    GPIO.cleanup()
# ============================
