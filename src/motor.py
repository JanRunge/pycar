from queue import Queue 
import threading
from datetime import datetime, timedelta
from time import sleep
import __main__
import sys

acceleration = True
message_type_throttle = "throttle"
message_type_increment = "increment"
message_type_power = "max_power"

direction_as_bool = {
    "forward" : True,
    "backward" : False 
}
def cond_log(motor, log):
   __main__.log(motor.char, log)

class Motor:
    # 
    def __init__(self, 
                forward_pin, 
                backward_pin,
                max_power, 
                increment_time, 
                name,
                increment = 0.05, 
                break_increment_time = 0.005, 
                accelerate=True, 
                min_power=0 ):

        self.forward_pin = forward_pin
        self.backward_pin = backward_pin
        self.max_power = max_power
        self.default_max_power = self.max_power
        self.queue = Queue()
        self.increment_time = increment_time
        self.break_increment_time = break_increment_time
        self.increment = increment
        self.running = threading.Event()
        self.last_message = 0    
        self.min_power = min_power
        self.name = name
        self.lock = threading.Lock()
        if not accelerate :
            increment_time = 0
            increment = 1
            break_increment_time = 0
        
        self.thread = __main__.create_thread(target = threaded_fun, args =(self,))

    
    def drive_forward(self ):
        self._put_queue_value((message_type_throttle, ("forward", self.max_power)))
    def drive_backward(self ):
        self._put_queue_value((message_type_throttle, ("backward", self.max_power)))
    def stop(self ):
        self._put_queue_value((message_type_throttle, (None, 0)))    
    def is_running(self):
        return self.running.is_set()

    def _put_queue_value(self, message):
        def message_is_redundant():
            return self.last_message == message

        if not message_is_redundant():
            __main__.log(self.name, "sending "+str(message)+ "to "+self.name +" worker")
            self.last_message = message
            self.queue.put(message)
            return True
        else:
        #print("not sending " +str(value))
            return False
    def _set_max_power(self, value):
        self.lock.acquire()
        self.max_power = value
        self.lock.release()
        self._put_queue_value((message_type_power, self.max_power))
    def _get_max_power(self):
        self.lock.acquire()
        val =  self.max_power
        self.lock.release()
        return val
    def boost(self, throttle):
        self.default_max_power = self.max_power
        self._set_max_power(throttle)
        

    def unboost(self):
        self._set_max_power(self.default_max_power)
    def disable_acceleration(self):
        self.queue.put((message_type_increment, 1))
    def enable_acceleration(self):
        self.queue.put((message_type_increment, self.increment))


def threaded_fun(motor):
    q = motor.queue
    current_direction = None
    current_throttle = 0
    direction, target_throttle =  ("forward", 0)
    bool_to_pin={
        True : motor.forward_pin,
        False : motor.backward_pin 
        }   
    increment_time = motor.increment_time
    break_increment_time = motor.break_increment_time
    min_power = motor.min_power
    increment =motor.increment
    stopping_threshold = 0.1
    last_increment = datetime.now() - timedelta(seconds=2)
    try:
        while True:
            if __main__.stop_application.isSet():
                cond_log(motor, "exit")
                sys.exit()
            while not q.empty():
                message_type, message_content = q.get()
                if message_type == message_type_throttle:
                    direction, target_throttle = message_content
                    divisor = 3
                elif message_type == message_type_increment:
                    increment = message_content
                elif message_type == message_type_power:
                    if target_throttle>0:
                        target_throttle= message_content
                        divisor = 3

            if direction is None: # wird übergeben, wenn gestoppt werden soll
                direction = current_direction
            current_direction_correct = current_direction is None or direction == current_direction
            direction_bool  = direction_as_bool[direction]
            if not current_direction_correct:
                
                pin_to_stop = bool_to_pin[not direction_bool]
                __main__.set_pin_value(pin_to_stop, 0)
                current_direction = None
                current_throttle = 0
            if target_throttle != 0:
                motor.running.set()
            else:
                motor.running.clear()
            current_direction = direction
            if target_throttle!=current_throttle:
                passed_seconds = (datetime.now() - last_increment).total_seconds()
                if current_throttle < target_throttle:
                    if passed_seconds >=increment_time:
                        if increment_time == 0:
                            current_throttle = target_throttle
                        else:
                            #set the next biggest number which is still <=1
                            current_throttle = min(1, current_throttle + increment , target_throttle)
                            current_throttle = max(current_throttle, min_power)
                    #acceleration mode
                elif current_throttle > target_throttle:
                    diff = current_throttle-target_throttle
                    if passed_seconds >=break_increment_time:
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
                pin_to_change = bool_to_pin[direction_bool]
                if current_throttle!=__main__.get_pin_value(pin_to_change):
                    __main__.set_pin_value(pin_to_change, current_throttle)
                    last_increment = datetime.now()
                sleep(min(break_increment_time,increment_time,0.1 ))
                #sleep for a short time (min(increment time, 100ms))
    except Exception as e:
        __main__.log(motor.name, "worker crashed")
        __main__.set_pin_value(motor.forward_pin, 0)
        __main__.set_pin_value(motor.backward_pin, 0)
        raise e
