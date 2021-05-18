#Bibliotheken einbinden
from gpiozero import LED, PWMLED, DistanceSensor
import RPi.GPIO as GPIO
import time
import config
import __main__
import threading

max_distance = 500
lock = threading.Lock()
#GPIO Modus (BOARD / BCM)

#Richtung der GPIO-Pins festlegen (IN / OUT)
led = PWMLED(config.pin_us_led)

GPIO.setmode(GPIO.BCM)
 
#GPIO Pins zuweisen
GPIO_TRIGGER = config.pin_us_trigger
GPIO_ECHO = config.pin_us_echo
 
#Richtung der GPIO-Pins festlegen (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)
#returns the distance in cm
def distanz():
    lock.acquire()
    GPIO.output(GPIO_TRIGGER, True)
 
    # setze Trigger nach 0.01ms aus LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
 
    StartZeit = time.time()
    StopZeit = time.time()
 
    # speichere Startzeit
    while GPIO.input(GPIO_ECHO) == 0:
        StartZeit = time.time()
 
    # speichere Ankunftszeit
    while GPIO.input(GPIO_ECHO) == 1:
        StopZeit = time.time()
    lock.release()
 
    # Zeit Differenz zwischen Start und Ankunft
    TimeElapsed = StopZeit - StartZeit
    # mit der Schallgeschwindigkeit (34300 cm/s) multiplizieren
    # und durch 2 teilen, da hin und zurueck
    distanz = (TimeElapsed * 34300) / 2
 
    return min(distanz, max_distance)

def us_thread_fun():
    while not __main__.stop_application.isSet():
        distance = distanz()
        show_on_led(distance)
        time.sleep(0.5)

def show_on_led(val):
    val = min(val, 100) # i dont care for anything thats more than 100 cm away
    l = abs(val-100)/100
    __main__.set_pin_value(led,l)


