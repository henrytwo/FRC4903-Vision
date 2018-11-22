import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
RED = 25
GREEN = 24
BLUE = 23
GPIO.setup(BLUE, GPIO.OUT)
GPIO.setup(RED, GPIO.OUT)
GPIO.setup(GREEN, GPIO.OUT)

# 1. Inititalizing (implied disabled)
# 3. Enabled (Unlocked/Locked)
# 4. Disabled
# 5. Error

#def network_ready():
#    print("NETWORK READY")
#    GPIO.output(GREEN, 0)
#    GPIO.output(BLUE, 0)
#    GPIO.output(RED, 123)
    #ORANGE

def locked():
    print('Locked on target')
    GPIO.output(GREEN, 255)
    GPIO.output(BLUE, 0)
    GPIO.output(RED, 0)
    #GREEN
def unlocked():
    print('Target not locked')
    GPIO.output(BLUE, 255)
    GPIO.output(GREEN, 0)
    GPIO.output(RED, 255)
    #PURPLE BUT IT LOOKS RED

def disabled():
    print('Disabled')
    GPIO.output(BLUE, 255)
    GPIO.output(GREEN, 0)
    GPIO.output(RED, 0)
    #BLUE
def error():
    print('Something went wrong')
    GPIO.output(RED, 255)
    GPIO.output(GREEN, 0)
    GPIO.output(BLUE, 0)
    #RED
def initializing():
    print('Initializing')
    GPIO.output(RED, 255)
    GPIO.output(GREEN, 255)
    GPIO.output(BLUE, 255)
    # WHITE
