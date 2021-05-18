from pyPS4Controller.controller import Controller
import __main__
from time import sleep
import sys

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
		__main__.drive_forward()
	def on_down_arrow_press(self):
		__main__.drive_backward()
	def on_left_arrow_press(self):
		__main__.steer_left()
	def on_right_arrow_press(self):
		__main__.steer_right()
	def on_up_down_arrow_release(self):
		__main__.drive_stop()
	def on_left_right_arrow_release(self):
		__main__.steer_stop()

	def on_L3_up(self, val):
		pass
	def on_L3_down(self, val):
		pass
	def on_L3_left(self, val):
		__main__.steer_left()
	def on_L3_right(self, val):
		__main__.steer_right()
	def on_L3_x_at_rest(self):
		__main__.steer_stop()

	def on_L2_release(self):
		__main__.drive_stop()
	def on_L2_press(self, val):
		__main__.drive_backward()
		
	def on_R2_release(self):
		__main__.drive_stop()
	def on_R2_press(self, val):
		__main__.drive_forward()

	#################
	# Special Controls#
	#################

	#x: boost
	def on_x_press(self):
		__main__.drive_motor.boost(1)
	def on_x_release(self):
		__main__.drive_motor.unboost()

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
		__main__.drive_forward()
		sleep(2)
		__main__.drive_backward()
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


def stop_ud():
	__main__.drive_stop()
def stop_lr():
	__main__.steer_stop()