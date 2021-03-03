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

with open('/opt/loxberry/config/plugins/gpio/pluginconfig.json') as json_pcfg_file:
    pcfg = json.load(json_pcfg_file)
    gpio = pcfg['gpio'];
    for channel in gpio['inputs']:
        print('pin: ' + p['pin'])
        print('wireing: ' + p['wiring'])


GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.IN, pull_up_down = GPIO.PUD_UP)

# ============================
def callback_input(channel):
 now = datetime.datetime.now()

 if GPIO.input(channel): # if SENSOR_PIN of channel == 1 or high
   #print now.strftime('%Y-%m-%d %H:%M:%S') + " : " + (MQTT_PATH_STATE_INPUT + str(channel) + ': ON')
   # publish.single(MQTT_PATH_STATE_INPUT + str(channel) + "/state" , "1", hostname=MQTT_SERVER)
   # publish.single(MQTT_PATH_STATE_INPUT + str(channel) + "/stateText" , "ON", hostname=MQTT_SERVER)
   # publish.single(MQTT_PATH_STATE_INPUT + str(channel) + "/timestamp_ON", now.strftime('%Y-%m-%d %H:%M:%S'), hostname=MQTT_SERVER)
   print (str(channel) + "high")
   time.sleep(SleepTimeL);
 else: # if SENSOR_PIN of channel != 1 or low
   #print now.strftime('%Y-%m-%d %H:%M:%S') + " : " + (MQTT_PATH_STATE_INPUT + str(channel) + ': OFF')
   # publish.single(MQTT_PATH_STATE_INPUT + str(channel) + "/stateText", "OFF", hostname=MQTT_SERVER)
   # publish.single(MQTT_PATH_STATE_INPUT + str(channel) + "/state", "0", hostname=MQTT_SERVER)
   # publish.single(MQTT_PATH_STATE_INPUT + str(channel) + "/timestamp_OFF", now.strftime('%Y-%m-%d %H:%M:%S'), hostname=MQTT_SERVER)
   print (str(channel) + "low")
   time.sleep(SleepTimeL);

def main():
    while 1:
        print ("while loop active")
        time.sleep(10);
# client = mqtt.Client()
#  client.on_connect = on_connect
 # client.on_message = on_message
# client.connect("localhost", 1883, 60)
# client.loop_forever()


if __name__ == '__main__':
    try:
        GPIO.add_event_detect(7 , GPIO.BOTH, callback=callback_input)
        main()
    except KeyboardInterrupt:
		GPIO.cleanup()
