from pyPS4Controller.controller import Controller
import __main__
from time import sleep

##########################################
#######   		Controller         #######
##########################################
class MyController(Controller):
	#https://pypi.org/project/pyPS4Controller/
	def __init__(self, **kwargs):
		Controller.__init__(self, **kwargs)

	#################
	# Basic Controls#
	#################
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

	def on_L2_release(self):
		char_released('s')
	def on_L2_press(self, val):
		char_pressed('s')
		
	def on_R2_release(self):
		char_released('w')
	def on_R2_press(self, val):
		char_pressed('w')

	#################
	# Special Controls#
	#################

	#x: boost
	def on_x_press(self):
		__main__.char_to_motor["w"].boost(1)
		__main__.char_to_motor["s"].boost(1)
	def on_x_release(self):
		__main__.char_to_motor["w"].unboost()
		__main__.char_to_motor["s"].unboost()

	# R1 / L1: increase / decrease power
	def on_R1_release(self):
		__main__.change_throttle_stage(1)
	def on_L1_release(self):
		__main__.change_throttle_stage(-1)

	# circle: toggle acceleration
	def on_circle_release(self):
		__main__.toggle_acceleration()
	def on_playstation_button_release(self):
		print("setting_stop_event")
		__main__.stop_application.set()
		sys.exit()


		

def disconnect():
	stop_ud()
	stop_lr()
	__main__.control_led.pwm(1)
	__main__.control_led.blink(0.1)
	sleep(10)
	__main__.stop_application.set()
	sys.exit()

def connect():
	__main__.control_led.off()
	__main__.set_control_led_to_throttle()

def start_controller():
	__main__.create_thread(target=_start_controller )

def _start_controller():
	if(__main__.testing):
		char_pressed("w")
		sleep(2)
		char_released("w")
		sleep(1)
		__main__.change_throttle_stage(-1)
	else:
		try:
			controller = MyController(interface="/dev/input/js0", connecting_using_ds4drv=False)
			# you can start listening before controller is paired, as long as you pair it within the timeout window
			controller.listen(timeout=90, on_connect=connect, on_disconnect=disconnect )
		except:
			print("got exception when trying to connect to controller. trying again in 1 sec")
			sleep(1)
			controller = MyController(interface="/dev/input/js0", connecting_using_ds4drv=False)
			# you can start listening before controller is paired, as long as you pair it within the timeout window
			controller.listen(timeout=90, on_connect=connect, on_disconnect=disconnect )


##########################################
#######Controller Helper Functions#######
##########################################

def char_pressed(char):
	__main__.char_to_motor[char].on()

def char_released(char):
	__main__.char_to_motor[char].off()
	
def stop_ud():
	char_released('w')
	char_released('s')
def stop_lr():
	char_released('a')
	char_released('d')