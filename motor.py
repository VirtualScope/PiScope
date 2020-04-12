import time              #time used to set sleep between motor commands
import RPi.GPIO as GPIO  #GPIO lib for Raspberry Pi (RPi3). Needed to use GPIO pins

    
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
# def menu():
#     #Simple menu used for testing
#     again = 'y'
#     while(again == 'y'):
#         direction = input("Up or down? (u or d) ")
#         x = stepperControl(stepCount,direction)
#         move(x)            
#         again = input('Go again? (y or n)')
#         GPIO.cleanup()
      
def main():
#     menu()
    moveMotorFromWeb(True,10)
        
if __name__ == '__main__': main()

