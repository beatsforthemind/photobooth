#!/usr/bin/python

import RPi.GPIO as gpio
import time

global gpio

gpio.cleanup()
gpio.setwarnings(False)
gpio.setmode(gpio.BCM)

# gpio.setup(22, gpio.IN)
# gpio.setup(22, gpio.IN, pull_up_down=gpio.PUD_UP)
# gpio.setup(22, gpio.IN, pull_up_down=gpio.PUD_DOWN)

gpio.setup(18, gpio.OUT)
gpio.output(18, gpio.LOW)
gpio.output(18, False)

while True:
	time.sleep(0.2)
	gpio.output(18, gpio.HIGH)
	gpio.output(18, True)
	time.sleep(0.2)
	gpio.output(18, gpio.LOW)
	gpio.output(18, False)

gpio.cleanup()
