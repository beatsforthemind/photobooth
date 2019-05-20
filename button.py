#!/usr/bin/python

import RPi.GPIO as gpio
import time

global gpio
gpio.setmode(gpio.BCM)
# gpio.setup(22, gpio.IN)
# gpio.setup(22, gpio.IN, pull_up_down=gpio.PUD_UP)
gpio.setup(22, gpio.IN, pull_up_down=gpio.PUD_DOWN)

input_value = gpio.input(22)

while True:
	print(str(input_value))
	input_value = gpio.input(22)
	time.sleep(0.25)

gpio.cleanup()

