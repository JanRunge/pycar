from queue import Queue
from datetime import datetime, timedelta
from time import sleep
from gpiozero import LED, PWMLED
import __main__
class Custom_led:
	def __init__(self, pin, testing, stop_application):
		if(testing):
			self.led = "customled"
		else:
			self.led = PWMLED(pin)
		
		self.queue = Queue()
		self.thread = __main__.create_thread(target = led_worker, args =(self.queue, self.led, stop_application))

	def on(self):
		print("on led")
		self.pwm(1)
	def off(self):

		print("off led")
		self.pwm(0)

	def blink(self, interval):
		print("blinking led")
		self.queue.put(("blink_interval", interval ))
	def disable_blink(self):
		print("disable blinking led")
		self.queue.put(("blink", False ))

	def pwm(self, value):
		print("pwm led")
		self.queue.put(("pwm", value))

def led_worker(q, led, stop_application):
	pwm_value = 0
	blinking = False
	blink_sleep = 0.0
	last_blink_change = datetime.now()
	sleeptime = 0.05
	while True:
		if stop_application.isSet():
			sys.exit()
		if q.empty()!=True:
			q_data = q.get()
			command, value = q_data
			if command == "pwm":
				pwm_value = value
			elif command == "blink_interval":
				blinking = True
				blink_sleep = value
			elif command == "blink":
				blinking = value
			else:
				print("led worker discarded message:")
				print(q_data)
		if blinking:
			sleeptime = blink_sleep
			delta_since_last_blink_change = (datetime.now() - last_blink_change).total_seconds()
			if delta_since_last_blink_change >= blink_sleep:
				last_blink_change = datetime.now()
				#change state
				if __main__.get_pin_value(led)==0:
					__main__.set_pin_value(led, pwm_value)
				else:
					__main__.set_pin_value(led, 0)
		else:
			sleeptime = 0.05
			if __main__.get_pin_value(led)!=pwm_value:
				__main__.set_pin_value(led,pwm_value)
		sleep(sleeptime)