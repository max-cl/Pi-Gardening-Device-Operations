#!/usr/bin/python3
import paho.mqtt.client as mqtt
import time
import json
from bson.objectid import ObjectId
import datetime
import socket
import os
import configparser
import board
import adafruit_dht

# Initial the dht device, with data pin connected to:
dhtDevice = adafruit_dht.DHT11(board.D4)

# Hostname
hostname = socket.gethostname()

# GENERAL CONFIG
config = configparser.RawConfigParser()
configDir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '../..', 'config.ini'))
config.read(configDir)

# SENSOR CONFIG
configSensor = configparser.RawConfigParser()
scriptDir = os.path.abspath(os.path.join(os.path.dirname( __file__ )))
configSensor.read(scriptDir+'/config.ini')

# Connection Variables to Broker 
brokerAddress = config.get('broker', 'brokerAddress')
brokerPort = config.get('broker', 'brokerPort')
brokerUsername = config.get('broker', 'brokerUsername')
brokerPassword = config.get('broker', 'brokerPassword')

### DEVICE AND SENSOR INFORMATION ###
deviceId = config.get('publisher', 'deviceId')
sensorId1 = configSensor.get('publisher', 'sensorId1')
sensorId2 = configSensor.get('publisher', 'sensorId2')

# Topic
sensorTopic = configSensor.get('topic', 'sensorTopic')
topic = hostname+"/"+sensorTopic

client = mqtt.Client(sensorId1+" and "+sensorId2)
client.username_pw_set(username=brokerUsername,password=brokerPassword)
client.connect(str(brokerAddress), int(brokerPort), 60)

def getTemperatureAndHumidity():
    # Print the values to the serial port
    temperature_c = dhtDevice.temperature
    temperature_f = temperature_c * (9 / 5) + 32
    humidity = dhtDevice.humidity
    print("Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(temperature_f, temperature_c, humidity))
    result = { "temperature": temperature_c, "humidity": humidity }
    return result

### LOGS ###
def generateLogName():
    global logName
    log_path = scriptDir+"/logs/"
    currentDT = str(datetime.date.today())
    currentDT = currentDT.replace('-', '_')
    currentDT = currentDT.replace(' ', '_')
    currentDT = currentDT.replace(':', '_')
    currentDT = currentDT.replace('.', '_')
    logName = log_path+'log' + currentDT + '.txt'


def addLogEntry(type, message):
    logFile = open(logName, 'a+')
    now = datetime.datetime.now()
    logFile.write('>' + str(now.strftime("%d-%m-%Y %H:%M:%S")) + ' | Type: ' + type + ' | ' + message + '\n')
    logFile.close()

#####################################################################################################################

if __name__ == '__main__':
    try:
        ### CREATE A NAME FILE LOG ###
        generateLogName()
        while True:
            # Datetime object containing current date and time
            now = datetime.datetime.now()
            # dd/mm/YY H:M:S
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            result = getTemperatureAndHumidity()
            data = json.dumps([{ "temperature": str(round(result["temperature"], 1)), "sensorId": ObjectId(sensorId1), "deviceId": ObjectId(deviceId), "date": dt_string }, { "humidity": str(round(result["humidity"], 1)), "sensorId": ObjectId(sensorId2), "deviceId": ObjectId(deviceId), "date": dt_string }], default=str)
            client.publish(topic, data)
            print("Just published " + str(result) + " to Topic: "+topic+" Date: "+dt_string)
            addLogEntry('Info', "Just published " + str(result) + " to Topic: "+topic+" Date: "+dt_string)
            time.sleep(10)

        # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        