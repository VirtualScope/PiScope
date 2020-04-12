import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)          #Set to physical pin location # instead of names
GPIO.setwarnings(False)           #Just here to keep warnings quiet

light = 21                        #Pin for hot wire on light. Groung at pin 20
GPIO.setup(light, GPIO.OUT)       #Set 'light' pin to output


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
    
def menu():
    again = 'y'
    while(again == 'y'):
        timer = input("Is there a timer? (y or n)")
        if timer == 'y':
            time = float(input("How much time in minutes? "))
            isPowered = 'off'
            x = LightControls(timer, time, isPowered)
            timerOn(x)
        else:
            isPowered = input("On or off? ")
            x = LightControls(timer, "", isPowered)
            noTimerSwitch(x)    
        again = input('Go again?  (y or n)')
      
def main():
    menu()    
        
if __name__ == '__main__': main()
