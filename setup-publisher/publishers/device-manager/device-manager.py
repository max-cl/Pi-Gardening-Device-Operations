#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import datetime
from pymongo import MongoClient
import socket
import os
import configparser
from pymongo import MongoClient
from bson.objectid import ObjectId
import json

# Hostname
hostname = socket.gethostname()

# Config reading and valuable
config = configparser.RawConfigParser()
configDir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'config.ini'))
config.read(configDir)

### BROKER CONNECTION ###
brokerAddress = config.get('broker', 'brokerAddress')
brokerPort = config.get('broker', 'brokerPort')
brokerUsername = config.get('broker', 'brokerUsername')
brokerPassword = config.get('broker', 'brokerPassword')

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    print("subscribing to: "+ str(hostname))
    client.subscribe([(str(hostname)+"/reboot",1),(str(hostname)+"/restart/dht11",1),(str(hostname)+"/restart/moisture",1),(str(hostname)+"/restart/ultrasonic",1),(str(hostname)+"/stop/dht11",1),(str(hostname)+"/stop/moisture",1),(str(hostname)+"/stop/ultrasonic",1)]) # QoS 0 = At most once, 1 = At least once , 2 = Exactly once

def on_message(client, userdata, message):
    topic = str(message.topic)
    message = str(message.payload.decode("utf-8"))
    print(topic +' '+ message)
    if topic == str(hostname)+"/reboot":
        os.system("systemctl reboot")
    elif topic == str(hostname)+"/restart/dht11":
        os.system("systemctl restart dht11.service")
    elif topic == str(hostname)+"/restart/moisture":
        os.system("systemctl restart moisture.service")
    elif topic == str(hostname)+"/restart/ultrasonic":
        os.system("systemctl restart ultrasonic.service")
    elif topic == str(hostname)+"/stop/dht11":
        os.system("systemctl stop dht11.service")
    elif topic == str(hostname)+"/stop/moisture":
        os.system("systemctl stop moisture.service")
    elif topic == str(hostname)+"/stop/ultrasonic":
        os.system("systemctl stop ultrasonic.service")


# Initialize the client that should connect to the Mosquitto broker
client = mqtt.Client(client_id=hostname+"-manager subscriber", protocol=mqtt.MQTTv31)
client.username_pw_set(username=brokerUsername,password=brokerPassword)
client.on_connect = on_connect
client.on_message = on_message
client.connect(str(brokerAddress), int(brokerPort), 60)

# Blocking loop to the Mosquitto broker
client.loop_forever()