from queue import Queue 
import threading
from datetime import datetime, timedelta
import __main__
import sys

acceleration = True

def cond_log(motor, log):
	if motor.char == "d" or motor.char == "a" :
		__main__.log(motor.char, log)

##########################################
#######        Motor Class         #######
##########################################
def motor_thread_fun(motor, stop_flag):
	q = motor.queue
	increment_time = motor.increment_time
	break_increment_time = motor.break_increment_time
	target_throttle = 0
	current_throttle = 0
	is_steering_motor = motor.is_steering_motor
	min_power = motor.min_power
	increment =motor.increment

	acceleration_mode = 1
	deceleration_mode = 0
	mode = acceleration_mode

	last_increment = datetime.now() - timedelta(seconds=2)
	while True:
		
		if __main__.stop_application.isSet():
			cond_log(motor, "exit")
			sys.exit()
		while q.empty()!=True:
			q_data = q.get()
			if q_data == stop_flag: 
				__main__.log(motor.char, " received stop_flag")
				motor.set_pin_value(0)
				target_throttle = 0
				current_throttle = 0
			else:
				#print(motor.char + "received "+ str(q_data))
				message_type, data = q_data
				if message_type == "throttle":
					target_throttle = data
					if data<current_throttle:
						mode = deceleration_mode
						divisor = 3
						stopping_threshold = 0.1
						diff = current_throttle-target_throttle

					if data>current_throttle:
						motor.counter.hard_stop()
						mode = acceleration_mode
				elif message_type == "increment":
					increment = data
		val = motor.get_pin_value()
		if val ==0:
			if not motor.stopped.isSet():
				motor.stopped.set()
				#print(motor.char+" is stopped")
		else:
			motor.stopped.clear()

		if target_throttle!=current_throttle:
			passed_seconds = (datetime.now() - last_increment).total_seconds()
			if mode == acceleration_mode and passed_seconds >=increment_time:
				if increment_time == 0:
					current_throttle = target_throttle
				else:
					#set the next biggest number which is still <=1
					current_throttle = min(1, current_throttle + increment , target_throttle)
					current_throttle = max(current_throttle, min_power)
			elif mode == deceleration_mode and passed_seconds >= break_increment_time:
				if break_increment_time == 0:
					current_throttle = target_throttle
				else:
					#stop if the remaining difference is < 0.1
					if diff<=stopping_threshold:
						current_throttle = target_throttle
					else:
						current_throttle = max(current_throttle - (diff/divisor), 0, target_throttle)
						diff = current_throttle-target_throttle
						divisor= divisor-0.5
			#set the pin value		
			#print(motor.char + str(current_throttle))
			if current_throttle!=motor.get_pin_value():
				motor.set_pin_value(current_throttle)
				last_increment = datetime.now()

class Motor:
	def __init__(self, _stop_flag, led_on, counter, max_power, increment_time, char, increment = 0.05, break_increment_time = 0.005, is_steering_motor = False, accelerate=True, min_power=0, ):
		self.pin = led_on
		self.counter = counter # ein motor
		self.max_power = max_power
		self.default_max_power = self.max_power
		self.accelerate = accelerate
		self.queue = Queue()
		self.increment_time = increment_time
		self.break_increment_time = break_increment_time
		self.increment = increment
		self.is_steering_motor = is_steering_motor
		self.stopped = threading.Event()
		self.turning_off = threading.Event()
		self.last_message = 0	
		self.char = char
		self.min_power = min_power
		self._stop_flag = _stop_flag
        
		if not accelerate :
			increment_time = 0
			increment = 1
			break_increment_time = 0
		
		print(self.pin)
		self.thread = __main__.create_thread(target = motor_thread_fun, args =(self,_stop_flag))

	def set_pin_value(self, x):
		return __main__.set_pin_value(self.pin, x)
	def get_pin_value(self):
		return __main__.get_pin_value(self.pin)

	def off(self):
		self.turning_off.set()
		self._put_queue_value(("throttle",0))
		
	def hard_stop(self):
		__main__.log(self.char,"hard stopping "+self.char)
		self.turning_off.set()
		if self._put_queue_value(self._stop_flag):
		#wait for the event (blocking)
			self.stopped.wait()
	def on(self):
		self.turning_off.clear()
		self._put_queue_value(("throttle",self.max_power))
		

	def boost(self, throttle):
		self.default_max_power = self.max_power
		self._set_max_power(throttle)
		

	def unboost(self):
		self._set_max_power(self.default_max_power)

	def _put_queue_value(self, value):
		def message_is_redundant():
			if value == self.last_message:
				return True
			if value == (("throttle", 0)) and self.last_message == self._stop_flag:
				return True
			if self.last_message == (("throttle", 0)) and value == self._stop_flag:
				return True
			return False

		if not message_is_redundant():
			__main__.log(self.char, "sending "+str(value)+ "to "+self.char +" worker")
			self.last_message = value
			self.queue.put(value)
			return True
		else:
			#print("not sending " +str(value))
			return False
	def _set_max_power(self, value):
		self.max_power = value
		if self.is_running() and not self.turning_off.isSet():
			#send the worker the new max power
			self.on()
	def _get_max_power(self):
		return self.max_power

	def is_running(self):
		return not self.stopped.isSet()

	def disable_acceleration(self):
		self.queue.put(("increment", 1))
	def enable_acceleration(self):
		self.queue.put(("increment", self.increment))

def toggle_acceleration():
	global acceleration
	if acceleration:
		#disable
		__main__.char_to_motor["w"].disable_acceleration()
		__main__.char_to_motor["s"].disable_acceleration()
		__main__.control_led.blink(0.3)
	else:
		#enable
		__main__.char_to_motor["w"].enable_acceleration()
		__main__.char_to_motor["s"].enable_acceleration()
		__main__.control_led.disable_blink()
	acceleration = not acceleration
