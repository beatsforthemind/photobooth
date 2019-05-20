#!/usr/bin/python

import RPi.GPIO as gpio
import time

global gpio
gpio.setmode(gpio.BCM)
gpio.cleanup()
