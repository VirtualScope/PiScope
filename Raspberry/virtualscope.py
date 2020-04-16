import sys
import os
import subprocess
import ftplib
import signal
from picamera import PiCamera
from time import sleep
#import mysql.connector
#from mysql.connector import Error
import datetime
import time                         #time used to set sleep between motor commands
import RPi.GPIO as GPIO             #GPIO lib for Raspberry Pi (RPi3). Needed to use GPIO pins
import threading                    #Threading for locks and spawning new threads

#Pi Control Server Imports
import json
import requests
from gevent.pywsgi import WSGIServer
from flask import Flask, request, jsonify
from flask_restful import Resource, Api


GPIO.setmode(GPIO.BOARD)            #Set to physical pin location # instead of names
GPIO.setwarnings(False)             #Just here to keep warnings quiet

light = 21                          #Pin for hot wire on light. Ground at pin 20
GPIO.setup(light, GPIO.OUT)         #Set 'light' pin to output

#Light Control code
class LightControls(object):
    lock = threading.RLock()     #One lock for the whole LightControls class
    
    def __init__(self, timer, time, isPowered):
        self.timer = timer
        self.time = time
        self.isPowered = isPowered
        
    def noTimerSwitch(x):
        if x.isPowered == True:
            GPIO.output(light, GPIO.HIGH)   #Set to high to turn on light
        if x.isPowered == False:
            GPIO.output(light, GPIO.LOW)    #Set to low (0v) to turn off light    


    def timerOn(x):
        maxTime = 3.0                       #Maximum time requested by Cindy Harley
        if x.time > maxTime:                #If user input time longer than maxTime...               
            x.time = maxTime                #time switched to maxTime
        timeout = time.time() + (60 * x.time)#Current time + specified timeout length
        GPIO.output(light, GPIO.HIGH)       #Set to high to turn on light    
        
        while time.time() <= timeout:       #Keep going until specified timeout
            time.sleep(0.0)                 #Does nothing.
        GPIO.output(light, GPIO.LOW)                   #isPowered always equals off at this point            

#Motor Code
class StepperControl(object):
    lock = threading.RLock()

    def __init__(self, stepCount):
        self.stepCount = stepCount
        if stepCount > 0:
            self.direction = True
        elif stepCount < 0:
            self.direction = False
            self.stepCount = abs(stepCount)
        else:
            return 
        
    def move(self):
        if (not self.lock.acquire(blocking=False)):
            print("{} could not get the lock for the motor.".format(threading.current_thread().name))
            return               #Someone already has the lock. Leave
        
        GPIO.setmode(GPIO.BOARD) #Set mode to read as physical pin layout instead of reference #s
        pins = [7,11,13,15]      #RPi3 physical #s for GPIO pins. Used for wiring motor to RPi3
        GPIO.setwarnings(False)
        # Set all motor pins to output
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)
        
        lowLimit = 10 #resistor side to 3.3V pin 1. Other side to GPIO pin 10
        highLimit = 12  # resistor side to pin 17.  Other side to GPIO pin 12
        
        #Set to input and low (0V) to begin.
        GPIO.setup(highLimit,GPIO.IN, pull_up_down = GPIO.PUD_DOWN) 
        GPIO.setup(lowLimit,GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
        
        #This is the half step sequence for a stepper motor. (See datasheet for motor)   
        halfStepSeq = [ [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0],
                        [0,0,1,0], [0,0,1,1], [0,0,0,1], [1,0,0,1]]
        
        #Reverse half step sequence for a stepper motor.
        revHalfStep = [ [1,0,0,1], [0,0,0,1], [0,0,1,1], [0,0,1,0],
                        [0,1,1,0], [0,1,0,0], [1,1,0,0], [1,0,0,0]]
        
        #Informs if limit switch has been hit
        limitFlag = False
        
        if self.direction == True:
            #Run loop for requested distance
            for i in range(self.stepCount):
                #If limit switch is hit (GPIO.HIGH), stop motor
                # REMOVE 'OR' TO FIT CIRCUMSTANCES WHEN LOW AND
                # HIGH ESTABLISHED ON MICROSCOPE
                if GPIO.input(highLimit)==GPIO.HIGH:
                    print("top limit switch hit")
                    limitFlag = True
                    break
                #If no limit switch is hit, run motor until destination is reached
                else:
                    #For loop to go through each halfstep in halfStepSeq array
                    for step in range(len(halfStepSeq)):
                        #For loop to set each pin to 1 or 0 corresponding with half step
                        # Example [1,0,0,0] pin 7=1, pin 11=0, pin 13=0, pin 15=0
                        for pin in range(len(pins)):
                            GPIO.output(pins[pin], halfStepSeq[step][pin])
                            #Time delay needed for motor to complete
                            #command before next sent
                            time.sleep(0.001)
                                            
                        
        if self.direction == False:            
            for i in range(self.stepCount):
                #If limit switch is hit (GPIO.HIGH), stop motor
                # REMOVE 'OR' TO FIT CIRCUMSTANCES WHEN LOW AND
                # HIGH ESTABLISHED ON MICROSCOPE
                if GPIO.input(lowLimit)==GPIO.HIGH:
                    print("bottom limit switch hit")
                    limitFlag = True
                    break 
                #If no limit switch is hit, run motor until destination is reached
                else:
                    for step in range(len(revHalfStep)):
                        #For loop to set each pin to 1 or 0 corresponding with half step
                        # Example [1,0,0,0] pin 7=1, pin 11=0, pin 13=0, pin 15=0
                        for pin in range(len(pins)):
                            GPIO.output(pins[pin], revHalfStep[step][pin])
                            #Time delay needed for motor to complete
                            #command before next sent
                            time.sleep(0.001)
                            
        self.lock.release()     #Remember to release the lock when finished!
        
#Start the control Server        
class DeviceComm(Resource):
    motorCalls = 0

    def start(self):
        app = Flask(__name__)
        api = Api(app)
        #ERROR_JSON = {'status':'error', 'message':'invalid input'}
        
        api.add_resource(DeviceComm, '/api/device/')
        
        print("Starting Web Server") # More secure web server instead of directly using Flask.
        
        http_server = WSGIServer(('0.0.0.0', 5000), app)
        http_server.serve_forever()
    def post(self):
        print("Recieved a request.")
        req = request.json # Note 'dict' is a python dictionary object.
        if req['device'] == 'light' and req['command'] == 'switch' and type(req['value']) == bool:
            #Start a new thread to test the light
            lightRequest = LightControls("", "", req['value']) # creates a new lightControls object
            lightThread = threading.Thread(target=LightControls.noTimerSwitch, kwargs=dict(self=lightRequest), name='lightThread')
            lightThread.start()
        elif req['device'] == 'motor' and req['command'] == 'move' and type(req['value']) == int:
            DeviceComm.motorCalls += 1
            threadName = 'motorThread' + str(DeviceComm.motorCalls)
            displacement = StepperControl(req['value'])
            motorThread = threading.Thread(target=StepperControl.move, kwargs=dict(self=displacement), name=threadName)
            motorThread.start()
        elif req['device'] == 'light' and req['command'] == 'timer' and type(req['value']) == float:
            lightRequest = LightControls(True, req['value'], True) # creates a new lightControls object
            lightThread = threading.Thread(target=LightControls.timerOn, kwargs=dict(self=lightRequest), name='lightThread')
            lightThread.start()

#Original pi code.
class scope(): 
    def __init__():
        #Define the microscope name !!IMPORTANT it comes from terminal argument
        my_name = sys.argv[1]

        #Establish the database connection
        try:
          connection = mysql.connector.connect(host='50.87.144.72',
                             database='teampuma_virtualscope',
                             user='teampuma_ryan',
                             password='ICS499')

          if connection.is_connected():
            #Select the time increment from the microscopes table
            cursor = connection.cursor()
            select_stmt = "SELECT picture_time_increment, youtube_stream FROM microscopes WHERE microscope_name = %(microscope_name)s"
            cursor.execute(select_stmt, { 'microscope_name': my_name })
            info = cursor.fetchone()
            time_increment = info[0]
            stream_link = info[1]

        #Error connecting -> Use default time_increment
        except Error as e:
          print("Error while connecting to MySQL", e)
          time_increment = 3
          
        #Close the database connection
        finally:
          if (connection.is_connected()):
            cursor.close()
            connection.close()

        #Connect to FTP server for file uploading
        ftp = ftplib.FTP()
        host = "ftp.virtualscope.site"
        port = 21
        ftp.connect(host, port)
        ftp.login("teampuma","1#%ekd%YlaG*")
        ftp.cwd("public_html/microscopes/" + my_name + "/images/")

        #The concatonated command for streaming
        stream_command = "raspivid -o - -t 0 -w 1280 -h 720 -fps 30 -b 6000000 | ffmpeg -re -f s16le -ac 2 -i /dev/zero -f h264 -i - -vcodec copy -g 50 -strict experimental -f flv " + stream_link

        #Picture folder where photos are saved on the Pi
        pic_folder = "/home/pi/MicroscopeImages/"

        #NEW: Start Control Server
        DeviceComm = threading.Thread(target=DeviceComm.start, args=(DeviceComm), name='DeviceCommMainThread')
        DeviceComm.start()

        while True:
          #Run stream for designated time interval
          pro = subprocess.Popen(stream_command, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid) 

          sleep((time_increment * 60)+3)
          os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
          
          #Define picture path and capture photo
          now = datetime.datetime.now() #Get timestamp
          picture_name = now.strftime("date_%m-%d-%Y_time_%H-%M-%S.jpg") #format image name
          picture_path = pic_folder + "current_image.jpg"
          camera = PiCamera()
          sleep(0.75)
          camera.capture(picture_path, resize=(1230, 924)) #take pictue and resize
          camera.close()
          
          #Send pic via ftp
          file = open(picture_path,"rb")                  # file to send
          ftp.storbinary("STOR " + picture_name, file)     # send the file
          file.close()
          
#scope_name = sys.argv[0]
#scope = scope(scope_name)

#NEW: Start Control Server
DeviceComm = threading.Thread(target=DeviceComm.start(DeviceComm), name='DeviceCommMainThread')
DeviceComm.start()
