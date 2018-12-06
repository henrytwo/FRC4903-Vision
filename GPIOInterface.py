try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    RED = 25
    GREEN = 24
    BLUE = 23
    GPIO.setup(BLUE, GPIO.OUT)
    GPIO.setup(RED, GPIO.OUT)
    GPIO.setup(GREEN, GPIO.OUT)
except:
    print('dis is not a da pi')

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
    try:
        GPIO.output(GREEN, 255)
        GPIO.output(BLUE, 0)
        GPIO.output(RED, 0)
    except:
        print('lol ur not a pi')
    #GREEN
def unlocked():
    print('Target not locked')
    try:
        GPIO.output(BLUE, 255)
        GPIO.output(GREEN, 0)
        GPIO.output(RED, 255)
    except:
        print('lol ur not a pi')
    #PURPLE BUT IT LOOKS RED

def disabled():
    print('Disabled')
    try:
        GPIO.output(BLUE, 255)
        GPIO.output(GREEN, 0)
        GPIO.output(RED, 0)
    except:
        print('lol ur not a pi')
    #BLUE
def error():
    print('Something went wrong')
    try:
        GPIO.output(RED, 255)
        GPIO.output(GREEN, 0)
        GPIO.output(BLUE, 0)
    except:
        print('lol ur not a pi')
    #RED
def initializing():
    print('Initializing')
    try:
        GPIO.output(RED, 255)
        GPIO.output(GREEN, 255)
        GPIO.output(BLUE, 255)
    except:
        print('lol ur not a pi')
    # WHITE
