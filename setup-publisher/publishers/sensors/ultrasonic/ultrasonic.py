#!/usr/bin/python3
import paho.mqtt.client as mqtt
import time
import json
from bson.objectid import ObjectId
import datetime
import os
import configparser
import RPi.GPIO as GPIO

### GPIO ###
# Disable warnings
GPIO.setwarnings(False)
#GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)
#set GPIO Pins
GPIO_TRIGGER = 18
GPIO_ECHO = 8
#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

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

def distance():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)

    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    StartTime = time.time()
    StopTime = time.time()

    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()

    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()

    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2

    return distance

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
            dist = distance()

            data = json.dumps({ "value": str(round(dist, 1)), "sensorId": ObjectId(sensorId), "deviceId": ObjectId(deviceId), "date": dt_string }, default=str)
            client.publish(topic, data)
            print("Just published " + str(round(dist, 1)) + " to Topic: "+topic+" Date: "+dt_string)
            addLogEntry('Info', "Just published " + str(round(dist, 1)) + " to Topic: "+topic+" Date: "+dt_string)
            time.sleep(10)

        # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()