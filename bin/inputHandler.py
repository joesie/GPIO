#!/usr/bin/python -u
############################################################
## Description
## GPIO-MQTT gateway
## usage: 		python GPIO_MQTT_PIR.py
## prerequisites: 	python, PIP
##			pip install rpi.gpio
## 			pip install paho-mqtt

import os
import socket
import paho.mqtt.client as mqtt
from time import sleep
import time
import datetime
import RPi.GPIO as GPIO
import paho.mqtt.publish as publish
import json

from threading import Thread
SleepTimeL = 0.2

#Configuration MQTT Topics
MQTT_SERVER             = "localhost"
#Output
MQTT_PATH_STATE_OUTPUT  = "gpio/Output/Pin_"
MQTT_PATH_CONFIG	    = "gpio/Configuration"
#Input
MQTT_PATH_STATE_INPUT   = "gpio/Input/Pin_"


# ============================
mqttpublish_auth = None;

def callback_input(channel):
 now = datetime.datetime.now()

 if GPIO.input(channel): # if SENSOR_PIN of channel == 1 or high
   print now.strftime('%Y-%m-%d %H:%M:%S') + " : " + (MQTT_PATH_STATE_INPUT + str(channel) + ': ON')
   publish.single(MQTT_PATH_STATE_INPUT + str(channel) + "/state" , "1", hostname=MQTT_SERVER, auth=mqttpublish_auth)
   publish.single(MQTT_PATH_STATE_INPUT + str(channel) + "/stateText" , "ON", hostname=MQTT_SERVER, auth=mqttpublish_auth)
   publish.single(MQTT_PATH_STATE_INPUT + str(channel) + "/timestamp_ON", now.strftime('%Y-%m-%d %H:%M:%S'), hostname=MQTT_SERVER, auth=mqttpublish_auth)

   time.sleep(SleepTimeL);

 else: # if SENSOR_PIN of channel != 1 or low
   print now.strftime('%Y-%m-%d %H:%M:%S') + " : " + (MQTT_PATH_STATE_INPUT + str(channel) + ': OFF')
   publish.single(MQTT_PATH_STATE_INPUT + str(channel) + "/stateText", "OFF", hostname=MQTT_SERVER, auth=mqttpublish_auth)
   publish.single(MQTT_PATH_STATE_INPUT + str(channel) + "/state", "0", hostname=MQTT_SERVER, auth=mqttpublish_auth)
   publish.single(MQTT_PATH_STATE_INPUT + str(channel) + "/timestamp_OFF", now.strftime('%Y-%m-%d %H:%M:%S'), hostname=MQTT_SERVER, auth=mqttpublish_auth)

   time.sleep(SleepTimeL);

# ============================

##
# setup GPIOS
##
GPIO.setmode(GPIO.BCM)
with open('/opt/loxberry/config/plugins/gpio/pluginconfig.json') as json_pcfg_file:
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

    # configure outputs
    outputs = gpio['outputs']
    for i in range(1, int(outputs['count'])):
        key = "channel_{}".format(i)
        channel = outputs[key]

        GPIO.setup(int(channel['pin']), GPIO.OUT)

# ============================

def on_connect(client, userdata, flags, rc):
    client.subscribe("gpio/Output/#")

# ============================
def on_message(client, userdata, msg):
#	print("Topic: " + msg.topic + " with Payload: " + str(msg.payload.decode("utf-8"))) + "!"
    mymsg = str(msg.payload.decode("utf-8"))
    mytopic = str(msg.topic)
#	print ("Topic: " + mytopic + " with Payload: " + mymsg + "!")
    now = datetime.datetime.now()

	# Search for topic in List of available output pins (BCM names) and set gpio to state LOW or HIGH
    for i in range(2, 27):
      print ("Output/Pin_" + str(i))
      if mytopic == "gpio/Output/Pin_" + str(i) :
        if mymsg == "ON" or mymsg == "1" or mymsg == "on" :
            GPIO.output(i, GPIO.LOW)
            time.sleep(SleepTimeL);
            print "Pin_" + str(i) + " on"
            publish.single(MQTT_PATH_STATE + str(i) + "/stateText", "on", hostname=MQTT_SERVER)
            publish.single(MQTT_PATH_STATE + str(i) + "/state", "1"     , hostname=MQTT_SERVER)
            publish.single(MQTT_PATH_STATE + str(i) + "/timestamp_ON" , now.strftime('%Y-%m-%d %H:%M:%S'), hostname=MQTT_SERVER)
    	    print (MQTT_PATH_STATE + str(i) + "/|-- Timestamp ON:" +  now.strftime('%Y-%m-%d %H:%M:%S'))

        if mymsg == "OFF" or mymsg == "0" or mymsg == "off":
            GPIO.output(i, GPIO.HIGH)
            time.sleep(SleepTimeL);
            print ("Pin_" + str(i) + " off")
            publish.single(MQTT_PATH_STATE + str(i) + "/stateText", "off", hostname=MQTT_SERVER)
            publish.single(MQTT_PATH_STATE + str(i) + "/state", "0"      , hostname=MQTT_SERVER)
            publish.single(MQTT_PATH_STATE + str(i) + "/timestamp_OFF"  , now.strftime('%Y-%m-%d %H:%M:%S'), hostname=MQTT_SERVER)
            print (MQTT_PATH_STATE + str(i) + "/|-- Timestamp OFF:" +  now.strftime('%Y-%m-%d %H:%M:%S'))

# ============================
with open('/opt/loxberry/data/system/plugindatabase.json') as json_plugindatabase_file:
    plugindatabase = json.load(json_plugindatabase_file)
    mqttconfigdir = plugindatabase['plugins']['07a6053111afa90479675dbcd29d54b5']['directories']['lbpconfigdir']
#TODO if no mqttconfig found, leave the script with an error
    mqttconfig = None
    with open(mqttconfigdir + '/mqtt.json') as json_mqttconfig_file:
        mqttconfig = json.load(json_mqttconfig_file)
#    print(json.dumps(mqttconfig, indent=4, sort_keys=True))

    mqttcred = None
    with open(mqttconfigdir + '/cred.json') as json_mqttcred_file:
        mqttcred = json.load(json_mqttcred_file)
#    print(json.dumps(mqttcred, indent=4, sort_keys=True))
    mqttuser = mqttcred['Credentials']['brokeruser']
    mqttpass = mqttcred['Credentials']['brokerpass']

    mqttpublish_auth = {
        'username':mqttuser,
        'password':mqttpass
    }
# ============================

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(mqttuser, mqttpass)
    client.connect(mqttconfig['Main']['brokeraddress'], 1883, 60)
    client.loop_forever()

# ============================


# if __name__ == '__main__':
#     try:
#
#         main()
#     except KeyboardInterrupt:
# 		GPIO.cleanup()
