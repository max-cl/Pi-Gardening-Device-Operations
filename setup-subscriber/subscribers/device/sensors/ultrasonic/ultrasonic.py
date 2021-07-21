#!/usr/bin/env python
import paho.mqtt.client as mqtt
import datetime
from pymongo import MongoClient
import socket
import os
import ConfigParser
from pymongo import MongoClient
from bson.objectid import ObjectId
import json

# Hostname
hostname = socket.gethostname()

# Config reading and valuable
config = ConfigParser.RawConfigParser()
configDir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '../../..', 'config.ini'))
config.read(configDir)

# SUBSCRIBER CONFIG
configDevice = ConfigParser.RawConfigParser()
configDeviceDir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '../..', 'config.ini'))
configDevice.read(configDeviceDir)

# SUBSCRIBER CONFIG
configSubscriber = ConfigParser.RawConfigParser()
scriptDir = os.path.abspath(os.path.join(os.path.dirname( __file__ )))
configSubscriber.read(scriptDir+'/config.ini')

### BROKER CONNECTION ###
brokerAddress = config.get('broker', 'brokerAddress')
brokerPort = config.get('broker', 'brokerPort')
brokerUsername = config.get('broker', 'brokerUsername')
brokerPassword = config.get('broker', 'brokerPassword')

### PUBLISHER ###
deviceId = configDevice.get('publisher', 'deviceId')

### TOPICS ###
sensorTopic = configSubscriber.get('topic', 'sensorTopic')

### MONGODB CONNECTION ###
dbAddress = config.get('database', 'dbAddress')
dbClient = config.get('database', 'dbClient')
dbCollectionName = config.get('database', 'dbCollectionName')
connectionTimeout = config.get('database', 'connectionTimeout')


def insert_document(collectionName, documentToInsert):
    collectionName.insert_one(documentToInsert)

def mongodb_connection(stringDBConnection, connectionTimeout):
    mongo_client = MongoClient(stringDBConnection,serverSelectionTimeoutMS=connectionTimeout,connectTimeoutMS=connectionTimeout,socketTimeoutMS=connectionTimeout) 
    return mongo_client

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    print("Topic: "+deviceId+"/"+sensorTopic)
    client.subscribe(deviceId+"/"+sensorTopic)

def on_message(client, userdata, msg):
    message=msg.payload.decode("utf-8")
    dataJson = json.loads(message)
    print({ "date": dataJson["date"], "sensorId": ObjectId(dataJson["sensorId"]), "deviceId": ObjectId(dataJson["deviceId"]), "value": float(dataJson["value"]) })
    insert_document(collection, { "date": str(dataJson["date"]), "sensorId": ObjectId(dataJson["sensorId"]), "deviceId": ObjectId(dataJson["deviceId"]), "value": float(dataJson["value"]) })


# Set up client for MongoDB
mongoClient = mongodb_connection(dbAddress, connectionTimeout)
db = mongoClient[dbClient]
collection = db[dbCollectionName]


# Initialize the client that should connect to the Mosquitto broker
client = mqtt.Client(client_id=hostname+" subscriber", protocol=mqtt.MQTTv31)
client.username_pw_set(username=brokerUsername,password=brokerPassword)
client.on_connect = on_connect
client.on_message = on_message
client.connect(brokerAddress, brokerPort, 60)

# Blocking loop to the Mosquitto broker
client.loop_forever()