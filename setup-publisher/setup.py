#!/usr/bin/python3
import os
import configparser
from pymongo import MongoClient
from bson.objectid import ObjectId

'''
publishers
 - config.ini (BrokerInfo, deviceId, autoStart)
 - sensor1/
 	- config.ini (SensorTopic, sensorId)
 	- sensor1.py
 	- service/
 		- sensor1.service
'''

def addPublisherServiceContent(serviceFileDir, publisherDir, sensorName):
	file = open(serviceFileDir, 'w+')
	file.write(
	'[Unit]'+ '\n' +
	'Description=Start '+ sensorName +' service' + '\n' 
	'## Make sure we only start the service after network is up' + '\n' +
	'Wants=network-online.target' + '\n' +
	'After=network.target' + '\n' + '\n' +

	'[Service]' + '\n' +
	'Type=oneshot' + '\n' +
	'ExecStart=/usr/bin/python3 '+publisherDir+'/'+sensorName+'.py' + '\n' + '\n' +

	'[Install]'+ '\n' +
	'WantedBy=multi-user.target')
	file.close()

def showSensorTypes():
	print(">Which kind of sensor do you want to add? (Choose an option)")
	print("[1] Temperature and Humidity sensor (DHT11)")
	print("[2] Moisture Sensor")
	print("[3] Wind Speed")
	print("[4] Water Pump")
	print("[5] Fan")
	print("[9] Ultrasonic Sensor (Only Testing purpuse)")

def changeSensorStatus(collectionName, deviceId, sensorId):
    collectionName.update_one(
            {
                "_id": ObjectId(deviceId),
                "sensors._id": ObjectId(sensorId),
            },
            {
                "$set": {

                    "sensors.$.status": True,
                },
            }
        )

def mongodbConnection(stringDBConnection, connectionTimeout):
    mongo_client = MongoClient(stringDBConnection,serverSelectionTimeoutMS=connectionTimeout,connectTimeoutMS=connectionTimeout,socketTimeoutMS=connectionTimeout) 
    return mongo_client

sensorsType = {
	"1": "dht11",
	"2": "moisture",
	"3": "wind",
	"4": "water",
	"5": "fan",
	"9": "ultrasonic"
}

currentDir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))
print("CurrentDir: "+currentDir)
print("Starting setup of Pi-Gardening-Operations")


print(">What do you want to setup?")
print("[1] Device (General configuration)")
print("[2] Add new publisher")
setupOptionSelected = str(input())
if(int(setupOptionSelected)==1):
	print("\n>Setting Up general configuration for Pi-Gardening-Operations")

	print("\n>Copying general config file.")
	os.system("mkdir -p "+currentDir+"/publishers/sensors")
	os.system("cp publishers/config.ini "+currentDir+"/publishers/")

	# Reading Config file
	config = configparser.RawConfigParser()
	config.read(currentDir + "/publishers/config.ini")

	print('>What is the Broker Address?')
	brokerAddress = str(input())

	print('>What is the Username (Credential Broker): ')
	brokerUsername = str(input())

	print('>What is the Password (Credential Broker): ')
	brokerPassword = str(input())

	print("\n>What is the Database Address? Input the entire URL: (mongodb://xxx:xxx@xx.xx.xx.xx:xxx/xxx)")
	dbAddress = str(input())
	
	print("\n>What is the Database Client:")
	dbClient = str(input())
	
	print("\n>What is the Collection Name:")
	dbCollectionName = str(input())

	print('>What is the Device Id (Raspberry Id registered in the DB): ')
	deviceId = str(input())

	print("\nSaving data to config")
	config.set("broker", 'brokerAddress', brokerAddress)
	config.set("broker", 'brokerUsername', brokerUsername)
	config.set("broker", 'brokerPassword', brokerPassword)
	config.set("database", 'dbAddress', dbAddress)
	config.set("database", 'dbClient', dbClient)
	config.set("database", 'dbCollectionName', dbCollectionName)
	config.set("publisher", 'deviceId', deviceId)
	with open(currentDir + "/publishers/config.ini", "w") as configFile:
		config.write(configFile)

	print("\n>Copying DEVICE-MANAGER service file.")
	os.system("sudo cp publishers/device-manager/service/device-manager.service /etc/systemd/system/")
	os.system("sudo systemctl daemon-reload")
	os.system("sudo systemctl enable device-manager.service")

	print(">Do you want to reboot the device?")
	print("[1] YES")
	print("[2] NO")
	doReboot = str(input())
	if int(doReboot) == 1:
		os.system("sudo systemctl reboot")
	else:
		print("GENERAL CONFIGURATION DONE!")

else:	
	showSensorTypes()
	sensorSelected = str(input())
	print("\n>Sensor selected: "+sensorSelected)

	sensorName = sensorsType[str(sensorSelected)]
	print("\n>Sensor Name: "+sensorName)

	if sensorName == "dht11":
		os.system("sudo pip3 install adafruit-circuitpython-dht")
		os.system("sudo pip3 install paho-mqtt")
		os.system("sudo pip3 install bson")
		os.system("sudo apt-get install libgpiod2")

	newPublisherDir = currentDir+"/publishers/sensors/"+sensorName
	os.system("mkdir -p "+newPublisherDir)
	print("\n>New directory created: "+newPublisherDir)

	serviceDir = newPublisherDir+"/service"
	os.system("mkdir "+serviceDir)
	os.system("touch "+serviceDir+"/"+sensorName+".service")
	
	print("\n>Setting up the "+sensorName+" service file.")
	# ADDING SERVICE CONTENT
	addPublisherServiceContent(serviceDir+"/"+sensorName+".service",newPublisherDir, sensorName)
	
	print("\n>Setting up the "+sensorName+" script file.")
	os.system("cp publishers/sensors/"+sensorName+"/"+sensorName+".py "+newPublisherDir+"/")
	os.system("cp publishers/sensors/"+sensorName+"/config.ini "+newPublisherDir+"/")

	print("\n>Adding a logs folder to the new PUBLISHER")
	os.system("mkdir "+newPublisherDir+"/logs")
	os.system("chmod -R 777 "+newPublisherDir+"/logs")

	# READING CONFIG SENSOR FILE
	config = configparser.RawConfigParser()
	config.read(newPublisherDir + "/config.ini")

	if sensorName == "dht11":
		print("\n>What is the Sensor Id for TEMPERATURE (DHT11) (Sensor Id registered in the DB): ")
		sensorId1 = str(input())
		print("\n>What is the Sensor Id for HUMIDITY (DHT11) (Sensor Id registered in the DB): ")
		sensorId2 = str(input())
		print("\n>Saving data to new PUBLISHER config")
		config.set("publisher", "sensorId1", sensorId1)
		config.set("publisher", "sensorId2", sensorId2)
	else:
		print("\n>What is the Sensor Id (Sensor Id registered in the DB): ")
		sensorId = str(input())
		print("\n>Saving data to new PUBLISHER config")
		config.set("publisher", "sensorId", sensorId)
	
	with open(newPublisherDir + "/config.ini", "w") as configFile:
		config.write(configFile)

	print("\n>Copying PUBLISHER service file.")
	os.system("sudo cp "+serviceDir+"/* /etc/systemd/system/")

	print("\n>Setting them up SERVICES.")
	os.system("sudo systemctl daemon-reload")
	os.system("sudo systemctl enable "+sensorName+".service")


	# READING GENERAL CONFIG FILE
	generalConfig = configparser.RawConfigParser()
	generalConfig.read(currentDir + "/publishers/config.ini")

	### MONGODB CONNECTION ###
	dbAddress = generalConfig.get('database', 'dbAddress')
	dbClient = generalConfig.get('database', 'dbClient')
	dbCollectionName = "devices"
	connectionTimeout = generalConfig.get('database', 'connectionTimeout')
	# DEVICE
	deviceId = generalConfig.get('publisher', 'deviceId')
	# MONGODB CONNECTION
	mongo_client = mongodbConnection(str(dbAddress), int(connectionTimeout))
	db = mongo_client[dbClient]
	collection = db[dbCollectionName]

	# UPDATE SENSOR STATUS AFTER SETTING UP THE CONFIGURATION FOR THE SENSOR (PUBLISHER)
	if sensorName == "dht11":
		changeSensorStatus(collection, deviceId, sensorId1)
		changeSensorStatus(collection, deviceId, sensorId2)
	else:
		changeSensorStatus(collection, deviceId, sensorId)


	# REBOOT DEVICE AFTER SET THE CONFIGURATION OF THE SENSOR (PUBLISHER)
	print(">Do you want to reboot the device?")
	print("[1] YES")
	print("[2] NO")
	doReboot = str(input())
	if int(doReboot) == 1:
		os.system("sudo systemctl reboot")
	else:
		print("Sensor "+sensorName+" (PUBLISHER) CONFIGURATION DONE!")
