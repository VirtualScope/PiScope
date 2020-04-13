import sys
import os
import subprocess
import ftplib
import signal
from picamera import PiCamera
from time import sleep
import mysql.connector
from mysql.connector import Error
import datetime
import time                         #time used to set sleep between motor commands
import RPi.GPIO as GPIO             #GPIO lib for Raspberry Pi (RPi3). Needed to use GPIO pins


GPIO.setmode(GPIO.BOARD)            #Set to physical pin location # instead of names
GPIO.setwarnings(False)             #Just here to keep warnings quiet

light = 21                          #Pin for hot wire on light. Groung at pin 20
GPIO.setup(light, GPIO.OUT)         #Set 'light' pin to output


class LightControls(object):
    def __init__(self, timer, time, isPowered):
        self.timer = timer
        self.time = time
        self.isPowered = isPowered
        
    def noTimerSwitch(x):
        if x.isPowered == 'on':
            GPIO.output(light, GPIO.HIGH)   #Set to high to turn on light
        if x.isPowered == 'off':
            GPIO.output(light, GPIO.LOW)    #Set to low (0v) to turn off light    
            
    def temporaryLightPowerTest(x): # Please delete this trash code of mine just making a POC
        if x == True:
            GPIO.output(light, GPIO.HIGH)   #Set to high to turn on light
        if x == False:
            GPIO.output(light, GPIO.LOW)    #Set to low (0v) to turn off light

    def timerOn(x):
        maxTime = 3.0                       #Maximum time requested by Cindy Harley
        if x.time > maxTime:                #If user input time longer than maxTime...               
            x.time = maxTime                #time switched to maxTime
        timeout = time.time() + (60 * x.time)#Current time + specified timeout length
        GPIO.output(light, GPIO.HIGH)       #Set to high to turn on light    
        
        while time.time() <= timeout:       #Keep going until specified timeout
            time.sleep(0.0)                 #Does nothing.
            
        noTimerSwitch(x)                    #isPowered always equals off at this point            


    def lightOnNoTimerWeb(newLightState):
        # Turn light on/off
        return True

    def lightWithTimerWeb(newLightState, timeInMinutes):
        # If variable is true, return false
        # Turn variable to true
        # Turn light on/off for x minutes
        return True

class stepperControl(object):
    def __init__(self, stepCount, direction):
        self.stepCount = stepCount
        self.direction = direction
    def move(x):    
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
        
        if x.direction == True:
            #Run loop for requested distance
            for i in range(x.stepCount):
                #If limit switch is hit (GPIO.HIGH), stop motor
                # REMOVE 'OR' TO FIT CIRCUMSTANCES WHEN LOW AND
                # HIGH ESTABLISHED ON MICROSCOPE
                if GPIO.input(highLimit)==GPIO.HIGH:
                    print("top limit switch hit")
                    limitFlag = True
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
                                            
                        
        if x.direction == False:            
            for i in range(x.stepCount):
                #If limit switch is hit (GPIO.HIGH), stop motor
                # REMOVE 'OR' TO FIT CIRCUMSTANCES WHEN LOW AND
                # HIGH ESTABLISHED ON MICROSCOPE
                if GPIO.input(lowLimit)==GPIO.HIGH:
                    print("bottom limit switch hit")
                    limitFlag = True 
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
                            
    def getMotorStatus():
        return int;
                            
    def moveMotorFromWeb(direction, duration):# Direct=Bool, Duration=int
        limit = False                        #Return value for success/failure of movement
        if duration > 1024:
            return limit 
        if direction == True:                #True == up
            x = stepperControl(duration, direction)
            limit = move(x)                  #Alters default value if hits limit switch
            return limit
            
        elif direction == False:                                #False == down
            x = stepperControl(duration, direction)
            limit = move(x)
            return limit
            
class DeviceComm:
    #TODO Kyle

class scope: 
    def __init__
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
scope_name = sys.argv[0]
scope = scope(scope_name)

