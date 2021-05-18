from gpiozero import LED, PWMLED
from gpiozero.pins.pigpio import PiGPIOFactory
import threading
from threading import Thread
from queue import Queue 
from datetime import datetime, timedelta
import sys
import time
import config


run_on_remote = False
remote_host = '192.168.2.209'
_stop_flag = object()
print("this is being run by ~/.config/autostart/pycar.desktop")
throttle_stages = [0.25, 0.35, 0.5, 0.7, 0.9, 1.0]
current_throttle_stage = 2
motor_speed_queue = Queue()
stop_application = threading.Event()
testing = config.testing

left = None
right = None
vor= None
back = None
control_led = None
control_led_secondary = None

drive_motor = None
steer_motor = None
acceleration=True


def get_pin_value(pin):
        if(testing == True):
                return pin
        else:
            return pin.value
def set_pin_value(pin, x):
        if(testing == True):
                pin = x
        else:
            pin.value = x

def create_thread(target, args =() ):
        thread = Thread(target = target, args =args)
        thread.start()
        return thread
##
# Custom imports
##
from control_led import Custom_led
import controller
import control_led
import motor
import ultrasonic

def log(motor, message):
        print("[ " + motor + " ] " + message)

def change_throttle_stage(by_amount):
        global current_throttle_stage
        global throttle_stages

        current_throttle_stage +=by_amount
        if len(throttle_stages) <= current_throttle_stage:
                current_throttle_stage = 0
        if current_throttle_stage<0:
                current_throttle_stage = len(throttle_stages) -1

        drive_motor._set_max_power(throttle_stages[current_throttle_stage])

        set_control_led_to_throttle()

        print("changed acceleration to " + str(throttle_stages[current_throttle_stage]))

def set_control_led_to_throttle():
        global current_throttle_stage
        global throttle_stages

        per_increment = 1.0 / len(throttle_stages)
        control_led.pwm(per_increment * (current_throttle_stage+1))
def toggle_acceleration():
	global acceleration
	if acceleration:
		#disable
		drive_motor.disable_acceleration()
		control_led.blink(0.3)
	else:
		#enable
		drive_motor.enable_acceleration()
		control_led.disable_blink()
	acceleration = not acceleration

def threaded_react_to_obstacle():
    w_motor= drive_motor
    obstacle_avoided = False
    old_power= 1
    while not stop_application.isSet():
        if(w_motor.is_running()):
            distance = ultrasonic.distanz()
            motor_power = w_motor._get_max_power()
            if(distance < motor_power*100):
                old_power= motor_power
                w_motor._set_max_power(max(motor_power/3, 0.15))
                set_control_led_to_throttle()
                obstacle_avoided = True
                print("obstacle avoided")
                control_led_secondary.on()
        if obstacle_avoided and distance>100:
            w_motor._set_max_power(old_power)
            obstacle_avoided = False
            control_led_secondary.off()

            time.sleep(0.1)
        else:
            time.sleep(1)


        
###########################################
####       on startup               #######
###########################################
def main():
    global left
    global right
    global vor
    global back
    global control_led
    global drive_motor
    global steer_motor
    global control_led_secondary

    if(run_on_remote):
        print("connecting with remote ... ")
        remote_factory = PiGPIOFactory(host=remote_host)
        left = PWMLED(config.pin_left, pin_factory=remote_factory) 
        right = PWMLED(config.pin_right, pin_factory=remote_factory)
        vor = PWMLED(config.pin_forward, pin_factory=remote_factory) 
        back = PWMLED(config.pin_backward, pin_factory=remote_factory) 
        print("connected")
    else:
        if (testing==False):
            left = PWMLED(config.pin_left) 
            right = PWMLED(config.pin_right)
            vor = PWMLED(config.pin_forward) 
            back = PWMLED(config.pin_backward) 
            control_led_secondary = Custom_led(config.pin_us_led, testing, stop_application)
            control_led = Custom_led(config.pin_control_led, testing, stop_application)
            control_led.on()
        else:
            left = 1
            right = 2
            vor = 3
            back = 4
            control_led = Custom_led(config.pin_control_led, testing, stop_application)

    drive_motor = motor.Motor(forward_pin   = vor, 
                              backward_pin  =back,
                              max_power = throttle_stages[current_throttle_stage],
                              increment_time = config.increment_time_drive,
                              name = "drive",
                              min_power = config.min_power_drive, 
                              break_increment_time = config.break_increment_time_drive
                              )
    steer_motor = motor.Motor(forward_pin   = left, 
                              backward_pin  = right,
                              max_power = config.max_power_steering,
                              increment_time = config.increment_time_steering,
                              name = "steer",
                              min_power = config.min_power_drive, 
                              break_increment_time = 0
                              )
    if config.use_distance_led:
        ultrasonic.setup()
        create_thread(ultrasonic.us_thread_fun)
    if config.avoid_obstacles:
        create_thread(threaded_react_to_obstacle)
    
    controller.start_controller()
    stop_application.wait()
    sys.exit()

def drive_forward():
    drive_motor.drive_forward()
def drive_backward():
    drive_motor.drive_backward()
def steer_left():
    steer_motor.drive_forward()
def steer_right():
    steer_motor.drive_backward()
def drive_stop():
    drive_motor.stop()
def steer_stop():
    steer_motor.stop()

main()