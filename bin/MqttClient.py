
import threading
from Channel import Channel, OutputChannel
import socket
import time
import json
import paho.mqtt.client as mqtt


class MqttClient():
    
    MQTT_DEFAULT_PORT = 1883
    client = None
    mqtt_heatbeatThread = None
    
    #Configuration MQTT Topics
    hostname = socket.gethostname() 
    MQTT_TOPIC_OUTPUT  = hostname + "/gpio/set/"
    MQTT_TOPIC_PWM = hostname + "/gpio/pwm/"
    MQTT_TOPIC_PWM_FREQUENCY = hostname + "/gpio/pwm/freq/"
    MQTT_TOPIC_PWM_DC = hostname + "/gpio/pwm/dc/"
    
    MQTT_RESPONSE_STATE = hostname + "/gpio/"
    
    _LOGGER = None

    #=============================
    # publish MQTT
    ##
    def publish(self, topic, payload=None, qos=0, retain=False, properties=None):
        self.client.publish(topic, payload=payload, qos=qos, retain=retain, properties=properties)

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
            self.client.publish(MqttClient.MQTT_RESPONSE_STATE+'status', "Online", retain = True)
            time.sleep(10)

    # ============================
    ##
    # definition of mqtt callbacks
    ##
    def on_connectCallback(self, client, userdata, flags, rc):
        client.subscribe(MqttClient.MQTT_TOPIC_OUTPUT + "#")
        client.subscribe(MqttClient.MQTT_TOPIC_PWM + "#")
        

    def on_messageCallback(self, client, userdata, msg):
        mymsg = str(msg.payload.decode("utf-8"))
        mytopic = str(msg.topic)
        self._LOGGER.debug("Topic: " + mytopic + " with Payload: " + mymsg + "!")

        if(mytopic.startswith(MqttClient.MQTT_TOPIC_OUTPUT + "json")):
            if(not mymsg):
                self.client.publish(MqttClient.MQTT_RESPONSE_STATE + "error" + "/stateText", "Error, can't set GPIO. For more information read the logfile!", retain = True)
                self._LOGGER.error('If you use json to set outputs, you have to transmit a json like {"5":"off","6":"on"}. For more information read the manual!')
                return
            try:
                msg_json = json.loads(mymsg)
                self._LOGGER.debug("msg_json: " + str(msg_json))
                for key in msg_json:
                    OutputChannel.handle_setOutput(key, msg_json[key])
                    self._LOGGER.debug("key: " + key + " msg_jsonkey] "+ str(msg_json[key]))
                return
            except json.decoder.JSONDecodeError as ex:
                self._LOGGER.exception("Malformed json given. Cannot parse string: " + mymsg)
            except Exception as e:
                self._LOGGER.exception(str(e))
                self.client.publish(MqttClient.MQTT_RESPONSE_STATE + "error" + "/stateText", "Error, can't set GPIO. For more information read the logfile!", retain = True)

        # Handle output Topic
        if(mytopic.startswith(MqttClient.MQTT_TOPIC_OUTPUT)):
            switched = False
            # Search for topic in List of available output pins and set gpio to state LOW or HIGH
            for channel in Channel.outputChannels:
                if mytopic == MqttClient.MQTT_TOPIC_OUTPUT + str(channel.pin) :
                    try:
                        channel.setOutput(channel, mymsg)
                        switched = True
                    except Exception as e:
                        self._LOGGER.exception(str(e))
                        self.client.publish(MqttClient.MQTT_RESPONSE_STATE + str(channel.pin) + "/stateText", "Error, can't set GPIO. For more information read the logfile!", retain = True)
            if switched == False:
                self.client.publish(MqttClient.MQTT_RESPONSE_STATE + "error" + "/stateText", "Error, unknown Topic: " + mytopic, retain = True)
        
        # Handle PWM Topic 
        if(mytopic.startswith(MqttClient.MQTT_TOPIC_PWM)):
            for channel in Channel.outputChannels:
                try:
                    #set frequency
                    if mytopic == MqttClient.MQTT_TOPIC_PWM_FREQUENCY + str(channel.pin) :
                        channel.setFrequency(mymsg)
                        self._LOGGER.debug("set frequency " + mymsg + " channel " + str(channel.pin))
                    #set duty cycle 
                    if mytopic == MqttClient.MQTT_TOPIC_PWM_DC + str(channel.pin) :   
                        channel.setDutyCycle(mymsg)
                        self._LOGGER.debug("set frequency " + mymsg + " channel " + str(channel.pin))
                except Exception as e:
                        self._LOGGER.exception(str(e))
                        self.client.publish(MqttClient.MQTT_RESPONSE_STATE + str(channel.pin) + "/stateText", "Error, can't set PWM. For more information read the logfile!", retain = True)


    def loop_forever(self):
            self.client.loop_forever()

    def disconnect(self):
        self.client.disconnect()   
        self.client.loop_stop() 
        self.mqtt_heatbeat._stop()

    def __init__(self, configfile, _LOGGER):
        self._LOGGER = _LOGGER
        self.client = mqtt.Client()
        mqttconf = self.createMqttConfig(configfile)
        MqttClient.hostname = socket.gethostname()

        if mqttconf is None:
            raise ValueError("No MQTT config found.")

        _LOGGER.info("start MQTT Client")

        self.client.on_connect = self.on_connectCallback
        self.client.on_message = self.on_messageCallback
        self.client.username_pw_set(mqttconf['username'], mqttconf['password'])
        self.client.will_set(MqttClient.MQTT_RESPONSE_STATE+'status', 'Offline', qos=0, retain=True)
        self.client.connect(mqttconf['address'], mqttconf['port'], 60)

        mqtt_heatbeatThread = threading.Thread(target=self.mqtt_heatbeat, args=(1,))
        mqtt_heatbeatThread.start()



        


