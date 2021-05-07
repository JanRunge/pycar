from gpiozero import LED, PWMLED
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
#from pynput.keyboard import Listener, Key
from pyPS4Controller.controller import Controller
import threading
from threading import Thread
import Queue 
import datetime

run_on_remote = False
remote_host = '192.168.2.209'
_stop_flag = object()
print("this is being run by ~/.config/autostart/pycar.desktop")



if(run_on_remote):
	print("connecting with remote ... ")
	remote_factory = PiGPIOFactory(host=remote_host)
	left = PWMLED(27, pin_factory=remote_factory) 
	right = PWMLED(22, pin_factory=remote_factory)
	vor = PWMLED(13, pin_factory=remote_factory) 
	back = PWMLED(19, pin_factory=remote_factory) 
	print("connected")
else:
	left = PWMLED(13) 
	right = PWMLED(19)
	vor = PWMLED(22) 
	back = PWMLED(27) 
	control_led = PWMLED(17)
	control_led.on()


#home = 192.168.2.205
#svenja = 192.168.178.41

throttle_stages = [0.2, 0.3, 0.5, 0.7, 0.9, 1.0]
current_throttle_stage = 2
class MyController(Controller):
	#https://pypi.org/project/pyPS4Controller/
	def __init__(self, **kwargs):
		Controller.__init__(self, **kwargs)

	
	##arrows
	def on_up_arrow_press(self):
		char_pressed('w')
	def on_down_arrow_press(self):
		char_pressed('s')
	def on_left_arrow_press(self):
		char_pressed('a')
	def on_right_arrow_press(self):
		char_pressed('d')
	def on_up_down_arrow_release(self):
		stop_ud()
	def on_left_right_arrow_release(self):
		stop_lr()

	
	def on_L3_left(self, val):
		char_pressed('a')
	def on_L3_right(self, val):
		char_pressed('d')
	def on_L3_x_at_rest(self):
		#print("releasing L3")
		stop_lr()
	#real           #in-Code
        #triangle       square
        #circle         triangle
        #X              circle
        #square         x
	def on_x_press(self):
		char_to_motor["w"].boost(1)
		char_to_motor["s"].boost(1)
	def on_x_release(self):
		char_to_motor["w"].unboost()
		char_to_motor["s"].boost(1)

	#real           #in code
	#l2 pressed     R3 right
	#l2 released    r3 x at rest -> r3 left
        #r2 pressed     r3 down
	#r2 released    r3 y at rest -> r3 up

	def on_L2_release(self):
		char_released('s')
	def on_L2_press(self, val):
		char_pressed('s')
		
	def on_R2_release(self):
		char_released('w')
	def on_R2_press(self, val):
		char_pressed('w')

	def on_R1_release(self):
		change_acceleration_stage()
		

def disconnect():
    print("disconnect")
    stop_ud()
    stop_lr()
    i = 1
    while i < 150:
        control_led.on()
        sleep(0.1)
        control_led.off()
        sleep(0.1)
        i += 1
# any code you want to run during loss of connection with the controller or keyboard interrupt
	pass
def connect():
    control_led.off()

def start_controller():
	controller = MyController(interface="/dev/input/js0", connecting_using_ds4drv=False)
	# you can start listening before controller is paired, as long as you pair it within the timeout window
	controller.listen(timeout=30, on_connect=connect, on_disconnect=disconnect )
	controllerThread = threading.Thread(target=start_controller )
	controllerThread.start()

def decelerate_sync(start_throttle, target_throttle, pin):
	start = datetime.datetime.now()
	current_throttle= start_throttle
	
	divisor = 3
	stopping_threshold = 0.1
	diff = current_throttle-target_throttle
	while current_throttle-target_throttle>0.1:
		current_throttle = current_throttle - (diff/divisor)
		pin.value = current_throttle
		diff = current_throttle-target_throttle
		divisor= divisor-0.5
		sleep(0.005)
	pin.value= target_throttle
	time_need = (datetime.datetime.now() - start).total_seconds()
	print("decelerated in " + str(time_need)+ " seconds")

def accelerate_fun(motor, stop_flag):
	q = motor.queue
	print("accelerating")
	max_throttle = motor.max_power
	
	increment = 0.05
	current_throttle = increment
	motor.pin.value = current_throttle
	last_increment = datetime.datetime.now()
	increment_time = motor.increment_time # wie viele sekunden zwischen den increments vergehen 
	print("time= "+str(increment_time))
	motor.counter.off()
	while True:
		if q.empty()!=True:
			q_data = q.get()
			if q_data == stop_flag: 
				decelerate_sync(current_throttle, 0, motor.pin)
				return
			else:
				if q_data<current_throttle:
					decelerate_sync(current_throttle,q_data, motor.pin)
				max_throttle = q_data
		secs = (datetime.datetime.now() - last_increment).total_seconds()
		if secs >=increment_time:
			print(str(current_throttle))
			if min(1, current_throttle + 0.1,max_throttle ) != current_throttle:
				current_throttle = min(1, current_throttle + 0.1,max_throttle )
				motor.pin.value = current_throttle
			last_increment = datetime.datetime.now()

class Motor:
	def __init__(self, led_on, led_off, max_power, accelerate, queue, increment_time):
		self.pin = led_on
		self.counter = led_off # ein motor
		self.max_power = max_power
		self.accelerate = accelerate
		self.thread = Thread(target = accelerate_fun, args =(self,_stop_flag ))
		self.queue = queue
		self.increment_time = increment_time
	def off(self):
		motor=self
		if motor.accelerate:
			if(motor.thread.isAlive()):
				motor.queue.put(_stop_flag)
				motor.thread.join()
				motor.queue.queue.clear()
				motor.thread = Thread(target = accelerate_fun, args =(self,_stop_flag ))
		else:
			motor.pin.value = 0
	def on(self):
		motor = self
		motor.counter.off()
		if motor.accelerate:
			if not motor.thread.isAlive():
				motor.thread.start()
		else:
			motor.pin.value = motor.max_power

	def boost(self, throttle):
		if self.accelerate:
			if self.thread.isAlive() and self.queue.empty():
				print("boost")
				self.queue.put(throttle)
			else:
				print("Boost discarded")
		else:
			print("Boost discarded 2")
	def unboost(self):
		if self.accelerate:
			if self.thread.isAlive() and self.queue.empty():
				print("boost")
				self.queue.put(self.max_power)



char_to_motor ={
	"w": Motor(vor, None, throttle_stages[current_throttle_stage], True, Queue.Queue(), 0.055),
	"s": Motor(back, None, 0.5, True, Queue.Queue(), 0.055),
	"a": Motor(left, None, 0.3, False, Queue.Queue(), 0),
	"d": Motor(right, None, 0.3, False,Queue.Queue(), 0)
}
char_to_motor["w"].counter = char_to_motor["s"]
char_to_motor["s"].counter = char_to_motor["w"]
char_to_motor["a"].counter = char_to_motor["d"]
char_to_motor["d"].counter = char_to_motor["a"]




#home = 192.168.2.205
#svenja = 192.168.178.41

def char_pressed(char):
	motor = char_to_motor[char]
	motor.on()

def char_released(char):
	print("turning off "+char)
	motor = char_to_motor[char]
	motor.off()
	

def stop_ud():
	char_released('w')
	char_released('s')
def stop_lr():
	char_released('a')
	char_released('d')

def change_acceleration_stage():
	global current_throttle_stage
	global throttle_stages
	current_throttle_stage +=1
	if len(throttle_stages) <= current_throttle_stage:
		current_throttle_stage = 0
	char_to_motor["w"].max_power = throttle_stages[current_throttle_stage]

	per_increment = 1.0 / len(throttle_stages)
	control_led.value = per_increment * (current_throttle_stage+1)
	print("changed acceleration to " + str(throttle_stages[current_throttle_stage]))


start_controller()


