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
import os

import getopt
import sys
import socket

SleepTimeL = 0.2

#Configuration MQTT Topics
hostname = socket.gethostname()
MQTT_TOPIC_OUTPUT  = hostname + "/gpio/set/"
MQTT_RESPONSE_STATE = hostname + "/gpio/"
MQTT_DEFAULT_PORT = 1883
client = mqtt.Client()


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

def mqtt_connectiondetails():
	LBSCONFIG = os.getenv('LBSCONFIG')
	generaljsonPath = LBSCONFIG+'/general.json'
	generaljsonFilehandle = open(generaljsonPath)
	generaljson = json.load(generaljsonFilehandle)

	sys.stderr.write ("Get LoxBerry MQTT Credentials from general.json\n")
	sys.stderr.write ("System config dir: " + LBSCONFIG + "\n")
	sys.stderr.write ("System config file: " + generaljsonPath + "\n")

	if "Mqtt" in generaljson:
		return generaljson['Mqtt']
	else:
		sys.stderr.write ("MQTT Gateway not installed\n")



# ============================
##
# get configuration from mqtt broker and store config in mqttconf variable
##
mqttconf = None

try:
    mqttcred = None
    mqttcred = mqtt_connectiondetails()

    sys.stderr.write( "Brokerhost: " + mqttcred['Brokerhost'] + "\n" )
    sys.stderr.write( "Brokerport: " + mqttcred['Brokerport'] + "\n" )
    sys.stderr.write( "Brokeruser: " + mqttcred['Brokeruser'] + "\n" )
    sys.stderr.write( "Brokerpass: " + mqttcred['Brokerpass'] + "\n" )
    sys.stderr.write( "Udpinport: " + mqttcred['Udpinport'] + "\n" )
    sys.stderr.write( "Websocketport: " + mqttcred['Websocketport'] + "\n" )

    mqttconf = {
        'username':mqttcred['Brokeruser'],
        'password':mqttcred['Brokerpass'],
        'address': mqttcred['Brokerhost'],
        'port': int( mqttcred['Brokerport'])
    }
    _LOGGER.debug("MQTT config" + str(mqttconf))
except Exception as e:
    _LOGGER.exception(str(e))

# If no mqtt config found leave the script with log entry
if mqttconf is None:
    _LOGGER.critical("No MQTT config found. Daemon stop working")
    sys.exit(-1)

#=============================
##
# send MQTT response for given pin and value
##
def send_mqtt_pin_value(pin, value):
    now = datetime.now()
    if(value):
        client.publish(MQTT_RESPONSE_STATE + str(pin) + "/state" , "1", retain = True)
        client.publish(MQTT_RESPONSE_STATE + str(pin) + "/stateText" , "ON", retain = True)
        client.publish(MQTT_RESPONSE_STATE + str(pin) + "/timestamp_ON", now.strftime('%Y-%m-%d %H:%M:%S'), retain = True)
        _LOGGER.debug(now.strftime('%Y-%m-%d %H:%M:%S') + " : " + (MQTT_RESPONSE_STATE + str(pin) + ': ON'))
    else:
        client.publish(MQTT_RESPONSE_STATE + str(pin) + "/stateText", "OFF", retain = True)
        client.publish(MQTT_RESPONSE_STATE + str(pin) + "/state", "0", retain = True)
        client.publish(MQTT_RESPONSE_STATE + str(pin) + "/timestamp_OFF", now.strftime('%Y-%m-%d %H:%M:%S'), retain = True)
        _LOGGER.debug( now.strftime('%Y-%m-%d %H:%M:%S') + " : " + (MQTT_RESPONSE_STATE + str(pin) + ': OFF'))

# ============================
##
# MQTT Heartbeat
#
def mqtt_heatbeat(name):
    while(1):
        client.publish(MQTT_RESPONSE_STATE+'status', "Online", retain = True)
        time.sleep(10)

##
# Callback function for interrupt handling
##
def callback_input(channel):
 now = datetime.now()

 if GPIO.input(channel): # if SENSOR_PIN of channel == 1 or high
    send_mqtt_pin_value(channel, 1)
    time.sleep(SleepTimeL);
 else: # if SENSOR_PIN of channel != 1 or low
   send_mqtt_pin_value(channel, 0)
   time.sleep(SleepTimeL);

# ============================
##
# setup GPIOS
##
_LOGGER.info("Configure GPIOs")
try:
    GPIO.setmode(GPIO.BCM)
    with open(configfile) as json_pcfg_file:
        pcfg = json.load(json_pcfg_file)
        _LOGGER.debug("Plugin Config: " + str(pcfg))
        gpio = pcfg['gpio']

        # configure inputs
        inputs = gpio['inputs']
        for i in range(0, int(inputs['count'])):
            key = "channel_{}".format(i)
            channel = inputs[key]

            wireing = GPIO.PUD_UP
            if channel['wiring'] == 'd':
                wireing = GPIO.PUD_DOWN

            GPIO.setup(int(channel['pin']), GPIO.IN, pull_up_down = wireing)
            GPIO.add_event_detect(int(channel['pin']) , GPIO.BOTH, callback=callback_input)
            _LOGGER.info("set Pin " + channel['pin'] + " as Input")

        # configure outputs
        outputs = gpio['outputs']
        for i in range(0, int(outputs['count'])):
            key = "channel_{}".format(i)
            channel = outputs[key]

            GPIO.setup(int(channel['pin']), GPIO.OUT)
            GPIO.output(int(channel['pin']), GPIO.HIGH) #Default GPIO High is off
            _LOGGER.info("set Pin " + channel['pin'] + " as Output")
except Exception as e:
    _LOGGER.exception(str(e))
# ============================
##
#   handle output command
##
def handle_setOutput(pin, value):
    if value == "ON" or value == "1" or value == "on" :
        GPIO.output(int(pin), GPIO.LOW)
        send_mqtt_pin_value(pin, 1)
    if value == "OFF" or value == "0" or value == "off":
        GPIO.output(int(pin), GPIO.HIGH)
        send_mqtt_pin_value(pin, 0)

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

    if(mytopic.startswith(MQTT_TOPIC_OUTPUT + "json")):
        if(not mymsg):
            client.publish(MQTT_RESPONSE_STATE + "error" + "/stateText", "Error, can't set GPIO. For more information read the logfile!", retain = True)
            _LOGGER.error('If you use json to set outputs, you have to transmit a json like {"5":"off","6":"on"}. For more information read the manual!')
            return
        try:
            msg_json = json.loads(mymsg)
            for key in msg_json:
                handle_setOutput(key, msg_json[key])
            return
        except json.decoder.JSONDecodeError as ex:
            _LOGGER.exception("Malformed json given. Cannot parse string: " + mymsg)
        except Exception as e:
            _LOGGER.exception(str(e))
            client.publish(MQTT_RESPONSE_STATE + "error" + "/stateText", "Error, can't set GPIO. For more information read the logfile!", retain = True)

	# Search for topic in List of available output pins (BCM names) and set gpio to state LOW or HIGH
    for i in range(0, 27):
        if mytopic == MQTT_TOPIC_OUTPUT + str(i) :
            try:
                handle_setOutput(i, mymsg)
            except Exception as e:
                _LOGGER.exception(str(e))
                client.publish(MQTT_RESPONSE_STATE + str(i) + "/stateText", "Error, can't set GPIO. For more information read the logfile!", retain = True)

#=============================
##
#  send the current state of configured inputs and outputs as MQTT message
##
def send_state():
    _LOGGER.debug("Send pin state ")
    if inputs is not None:
        _LOGGER.debug("Send pin state for inputs")
        for i in range(0, int(inputs['count'])):
            key = "channel_{}".format(i)
            channel = inputs[key]
            value = GPIO.input(int(channel['pin']))
            send_mqtt_pin_value(int(channel['pin']), value)

    if outputs is not None:
        _LOGGER.debug("Send pin state for outputs")
        for i in range(0, int(outputs['count'])):
            key = "channel_{}".format(i)
            channel = outputs[key]
            value = GPIO.input(int(channel['pin']))
            # invert value because a LOW value means the output is ON
            send_mqtt_pin_value(int(channel['pin']), not value)
# ============================
##
# start mqtt Client
##
try:
    _LOGGER.info("start MQTT Client")

    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(mqttconf['username'], mqttconf['password'])
    client.will_set(MQTT_RESPONSE_STATE+'status', 'Offline', qos=0, retain=True)
    client.connect(mqttconf['address'], mqttconf['port'], 60)

    mqtt_heatbeatThread = threading.Thread(target=mqtt_heatbeat, args=(1,))
    mqtt_heatbeatThread.start()
    send_state()
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
