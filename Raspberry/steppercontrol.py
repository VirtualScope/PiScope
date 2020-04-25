import time                         #time used to set sleep between motor commands
import RPi.GPIO as GPIO             #GPIO lib for Raspberry Pi (RPi3). Needed to use GPIO pins
import threading                    #Threading for locks and spawning new threads

GPIO.setmode(GPIO.BOARD)            #Set to physical pin location # instead of names
GPIO.setwarnings(False)             #Just here to keep warnings quiet

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