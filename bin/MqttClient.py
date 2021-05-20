
import threading
from Channel import Channel, OutputChannel
import socket
import time
import json
import paho.mqtt.client as mqtt


class MqttClient(mqtt.Client):
    
    MQTT_DEFAULT_PORT = 1883
    
    #Configuration MQTT Topics
    hostname = None 
    MQTT_TOPIC_OUTPUT  = hostname + "/gpio/set/"
    MQTT_RESPONSE_STATE = hostname + "/gpio/"
    
    _LOGGER = None

    # ============================
    ##
    # get configuration from mqtt broker and store config in mqttconf variable
    ##
    def createMqttConfig(self, configfile):    

        try:
            mqttconf = None
            with open(configfile) as json_plugindatabase_file:
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
                mqttPort = MqttClient.MQTT_DEFAULT_PORT
                if len(mqttaddressArray) > 1:
                    mqttPort = int(mqttaddressArray[1])

                mqttconf = {
                    'username':mqttuser,
                    'password':mqttpass,
                    'address': mqttaddressArray[0],
                    'port': mqttPort
                }
            self._LOGGER.debug("MQTT config" + str(mqttconf))

            return mqttconf
        except Exception as e:
            self._LOGGER.exception(str(e))

    
    
    # ============================
    ##
    # MQTT Heartbeat
    #
    def mqtt_heatbeat(self, name):
        while(1):
            self.publish(MqttClient.MQTT_RESPONSE_STATE+'status', "Online", retain = True)
            time.sleep(10)

    # ============================
    ##
    # definition of mqtt callbacks
    ##
    def on_connect(self, client, userdata, flags, rc):
        self.subscribe(MqttClient.MQTT_TOPIC_OUTPUT + "#")
        

    def on_message(self, client, userdata, msg):
        mymsg = str(msg.payload.decode("utf-8"))
        mytopic = str(msg.topic)
        self._LOGGER.debug("Topic: " + mytopic + " with Payload: " + mymsg + "!")

        if(mytopic.startswith(MqttClient.MQTT_TOPIC_OUTPUT + "json")):
            if(not mymsg):
                self.publish(MqttClient.MQTT_RESPONSE_STATE + "error" + "/stateText", "Error, can't set GPIO. For more information read the logfile!", retain = True)
                self._LOGGER.error('If you use json to set outputs, you have to transmit a json like {"5":"off","6":"on"}. For more information read the manual!')
                return
            try:
                msg_json = json.loads(mymsg)
                for key in msg_json:
                    OutputChannel.handle_setOutput(key, msg_json[key])
                return
            except json.decoder.JSONDecodeError as ex:
                self._LOGGER.exception("Malformed json given. Cannot parse string: " + mymsg)
            except Exception as e:
                self._LOGGER.exception(str(e))
                self.publish(MqttClient.MQTT_RESPONSE_STATE + "error" + "/stateText", "Error, can't set GPIO. For more information read the logfile!", retain = True)

        # Search for topic in List of available output pins (BCM names) and set gpio to state LOW or HIGH
        for i in range(0, 27):
            if mytopic == MqttClient.MQTT_TOPIC_OUTPUT + str(i) :
                try:
                    OutputChannel.handle_setOutput(i, mymsg)
                except Exception as e:
                    self._LOGGER.exception(str(e))
                    self.publish(MqttClient.MQTT_RESPONSE_STATE + str(i) + "/stateText", "Error, can't set GPIO. For more information read the logfile!", retain = True)



    def __init__(self, configfile, _LOGGER):
        mqttconf = self.createMqttConfig(configfile, _LOGGER)
        MqttClient.hostname = socket.gethostname()

        if mqttconf is None:
            raise ValueError("No MQTT config found.")

        _LOGGER.info("start MQTT Client")

        super().on_connect = self.on_connect
        super().on_message = self.on_message
        self.username_pw_set(mqttconf['username'], mqttconf['password'])
        self.will_set(MqttClient.MQTT_RESPONSE_STATE+'status', 'Offline', qos=0, retain=True)
        self.connect(mqttconf['address'], mqttconf['port'], 60)

        mqtt_heatbeatThread = threading.Thread(target=self.mqtt_heatbeat, args=(1,))
        mqtt_heatbeatThread.start()

        Channel.sendChannelStates()


        


