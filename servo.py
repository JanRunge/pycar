#Importing the necessary library
import RPi.GPIO as GPIO
from time import sleep

#Reference by GPIOs IDs
GPIO.setmode(GPIO.BCM)

#Assigning the GPIOs to the Lego's command wires
C1 = 12
C2 = 16
moveFactor = 14.285714286

#Setting up the necessary GPIOs
GPIO.setup(C1, GPIO.OUT)
GPIO.setup(C2, GPIO.OUT)

#Setting up the PWMs - (GPIO ID, Frequency)
f = 3000
pwm1 = GPIO.PWM(C1, f)
pwm2 = GPIO.PWM(C2, f)


def setPosition(position):
    pwm1.stop()
    pwm2.stop()
    i = round(position * moveFactor, 2)

    if position >= 0:
        print 'Position: ' + str(position) + ' at a Duty Cycle of ' + str(i)
        pwm1.start(i)
    else:
        print 'Position: ' + str(position) + ' at a Duty Cycle of ' + str(i*-1)
        pwm2.start(i*-1)

#Testing the commands with a LED
try:
    setPosition(-7)   #180 Degrees
    sleep(1)
    setPosition(-1)   #180 Degrees
    sleep(1)
    setPosition(7)    #0 Degree
    sleep(1)
except:
    pass

pwm1.stop()     # Back to the normal position (90 degrees)
pwm2.stop()
GPIO.cleanup()
