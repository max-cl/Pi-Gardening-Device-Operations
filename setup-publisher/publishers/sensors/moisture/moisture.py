#!/usr/bin/python3
import paho.mqtt.client as mqtt
import time
import json
from bson.objectid import ObjectId
import datetime
import os
import configparser
import RPi.GPIO as GPIO

#GPIO SETUP
# Define the GPIO pin that we have our digital output from our sensor connected to
channel = 21
# Set our GPIO numbering to BCM
GPIO.setmode(GPIO.BCM)
# Set the GPIO pin to an input
GPIO.setup(channel, GPIO.IN)

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
sensorId = configSensor.get('publisher', 'sensorId')

# Topic
sensorTopic = configSensor.get('topic', 'sensorTopic')
topic = deviceId+"/"+sensorTopic

client = mqtt.Client(sensorId)
client.username_pw_set(username=brokerUsername,password=brokerPassword)
client.connect(str(brokerAddress), int(brokerPort), 60)

def getMoisture(channel):
    # Datetime object containing current date and time
    now = datetime.datetime.now()
    # dd/mm/YY H:M:S
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    
    if GPIO.input(channel):
        result = 1  # No water Detected
    else:
        result = 0  # Water Detected

    data = json.dumps({ "value": str(result), "sensorId": ObjectId(sensorId), "deviceId": ObjectId(deviceId), "date": dt_string }, default=str)
    client.publish(topic, data)
    print("Just published " + str(result) + " to Topic: "+topic+" Date: "+dt_string)
    addLogEntry('Info', "Just published " + str(result) + " to Topic: "+topic+" Date: "+dt_string)

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

# This line tells our script to keep an eye on our gpio pin and let us know when the pin goes HIGH or LOW
GPIO.add_event_detect(channel, GPIO.BOTH, bouncetime=300)
# This line asigns a function to the GPIO pin so that when the above line tells us there is a change on the pin, run this function
GPIO.add_event_callback(channel, getMoisture)

if __name__ == '__main__':
    try:
        ### CREATE A NAME FILE LOG ###
        generateLogName()
        while True:
            time.sleep(1)

        # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()