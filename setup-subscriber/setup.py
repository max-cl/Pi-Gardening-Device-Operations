#!/usr/bin/python
import os
import ConfigParser

'''
subscribers
 - config.ini (BrokerInfo, Database (MongoDB))
 - device/
 	- config.ini (SensorTopic, sensorId)
    - sensors/
        - sensor1.py
        - service/
            - sensor1.service
'''

def addSubscriberServiceContent(serviceFileDir, subscribeDir, sensorName, hostnameDevice):
	file = open(serviceFileDir, 'w+')
	file.write(
	'[Unit]'+ '\n' +
	'Description=Start '+ sensorName +' service (' + hostnameDevice + ')\n' 
	'## Make sure we only start the service after network is up' + '\n' +
	'Wants=network-online.target' + '\n' +
	'After=network.target' + '\n' + '\n' +

	'[Service]' + '\n' +
	'Type=oneshot' + '\n' +
	'ExecStart=/usr/bin/python '+subscribeDir+'/'+sensorName+'.py' + '\n' + '\n' +

	'[Install]'+ '\n' +
	'WantedBy=multi-user.target')
	file.close()

def showSensorTypes():
	print(">Which kind of sensor do you want to subscribe to? (Choose an option)")
	print("[1] Temperature and Humidity sensor (DHT11)")
	print("[2] Moisture Sensor")
	print("[3] Wind Speed")
	print("[4] Water Pump")
	print("[5] Fan")
	print("[9] Ultrasonic Sensor (Only Testing purpuse)")

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
print("[1] General configuration (BrokerInfo & DB)")
print("[2] Add a new Device")
setupOptionSelected = str(raw_input())
if(int(setupOptionSelected)==1):

    print("\n>Copying general config file.")
    os.system("mkdir -p "+currentDir+"/subscribers")
    os.system("cp subscribers/config.ini "+currentDir+"/subscribers/")

    # Reading Config file
    config = ConfigParser.RawConfigParser()
    config.read(currentDir + "/subscribers/config.ini")

    print("\n>Starting setup of Pi-Gardening Operations (Subscriber)")

    print("\n>What is the Broker Address?")
    brokerAddress = str(raw_input())

    print("\n>What is the Username: (Credential Broker)")
    brokerUsername = str(raw_input())

    print("\n>What is the Password: (Credential Broker)")
    brokerPassword = str(raw_input())

    print("\n>What is the Database Address? Input the entire URL: (mongodb://xxx:xxx@xx.xx.xx.xx:xxx/xxx)")
    dbAddress = str(raw_input())

    print("\n>What is the Database Client:")
    dbClient = str(raw_input())

    print("\n>What is the Collection Name:")
    dbCollectionName = str(raw_input())


    print("\n>Saving data to config")
    config.set("broker", "brokerAddress", brokerAddress)
    config.set("broker", "brokerUsername", brokerUsername)
    config.set("broker", "brokerPassword", brokerPassword)

    config.set("database", "dbAddress", dbAddress)
    config.set("database", "dbClient", dbClient)
    config.set("database", "dbCollectionName", dbCollectionName)

    with open(currentDir + "/subscribers/config.ini", "w") as configFile:
        config.write(configFile)
else:
    print("\n>Copying general config file.")
    os.system("mkdir -p "+currentDir+"/subscribers/device")
    os.system("cp subscribers/device/config.ini "+currentDir+"/subscribers/device/")

    # Reading Config file
    config = ConfigParser.RawConfigParser()
    config.read(currentDir + "/subscribers/device/config.ini")

    print("\n>What is the Hostname of the new Device:")
    hostnamePublisher = str(raw_input())

    print("\n>Saving data to config")
    config.set("publisher", "hostnamePublisher", hostnamePublisher)

    with open(currentDir + "/subscribers/device/config.ini", "w") as configFile:
        config.write(configFile)

    os.system("mv "+currentDir+"/subscribers/device "+currentDir+"/subscribers/"+hostnamePublisher)
    os.system("mkdir -p "+currentDir+"/subscribers/"+hostnamePublisher+"/sensors")

    showSensorTypes()
    sensorSelected = str(raw_input())
    print("\n>Sensor selected: "+sensorSelected)

    sensorName = sensorsType[str(sensorSelected)]
    print("\n>Sensor Name: "+sensorName)

    newSubscribeDir = currentDir+"/subscribers/"+hostnamePublisher+"/sensors/"+sensorName
    os.system("mkdir -p "+newSubscribeDir)
    print("\n>New subscriber directory created: "+newSubscribeDir)

    serviceDir = newSubscribeDir+"/service"
    os.system("mkdir "+serviceDir)
    os.system("touch "+serviceDir+"/"+hostnamePublisher+"-"+sensorName+".service")

    print("\n>Setting up the "+sensorName+" service file.")
	# Adding Service Content 
    addSubscriberServiceContent(serviceDir+"/"+hostnamePublisher+"-"+sensorName+".service",newSubscribeDir, sensorName, hostnamePublisher)

    print("\n>Setting up the "+sensorName+" script file from Device "+hostnamePublisher+".")
    os.system("cp subscribers/device/sensors/"+sensorName+"/"+sensorName+".py "+newSubscribeDir+"/")
    os.system("cp subscribers/device/sensors/"+sensorName+"/config.ini "+newSubscribeDir+"/")

    print("\n>Adding a logs folder to the new SUBSCRIBER")
    os.system("mkdir "+newSubscribeDir+"/logs")
    os.system("chmod -R 777 "+newSubscribeDir+"/logs")

    print("\n>Copying service file and setting them up")
    os.system("sudo cp "+serviceDir+"/* /etc/systemd/system/")
    os.system("sudo systemctl daemon-reload")
    os.system("sudo systemctl enable "+hostnamePublisher+"-"+sensorName+".service")
