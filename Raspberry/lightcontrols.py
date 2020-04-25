import datetime
import time                         #time used to set sleep between motor commands
import RPi.GPIO as GPIO             #GPIO lib for Raspberry Pi (RPi3). Needed to use GPIO pins
import threading                    #Threading for locks and spawning new threads

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
        
    def noTimerSwitch(self):
        if self.isPowered == True:
            GPIO.output(light, GPIO.HIGH)   #Set to high to turn on light
        if self.isPowered == False:
            GPIO.output(light, GPIO.LOW)    #Set to low (0v) to turn off light    


    def timerOn(self):
        maxTime = 3.0                       #Maximum time requested by Cindy Harley
        if self.time > maxTime:                #If user input time longer than maxTime...               
            self.time = maxTime                #time switched to maxTime
        timeout = time.time() + (60 * self.time)#Current time + specified timeout length
        GPIO.output(light, GPIO.HIGH)       #Set to high to turn on light    
        
        while time.time() <= timeout:       #Keep going until specified timeout
            time.sleep(0.0)                 #Does nothing.
        GPIO.output(light, GPIO.LOW)                   #isPowered always equals off at this point   