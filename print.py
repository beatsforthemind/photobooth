#!/usr/bin/python

#IMPORTS
import RPi.GPIO as gpio
import picamera
import pygame
import time
import os

# import Image
# import ImageDraw

import cups
import logging
import signal

from threading import Thread
from pygame.locals import *
from time import sleep

import PIL.Image
# from PIL import Image
from PIL import Image, ImageDraw

from signal import alarm, signal, SIGALRM, SIGKILL

conn = cups.Connection()
printers = conn.getPrinters()
printer_name = printers.keys()[0]

print(str(printer_name))

#Print the file
printqueuelength = len(conn.getJobs())

#If multiple prints in the queue error
if  printqueuelength > 1:
	Message = "PRINT ERROR"
	conn.enablePrinter(printer_name)
elif printqueuelength == 1:
	SmallMessage = "Print Queue Full!"
	conn.enablePrinter(printer_name)

# conn.printFile(printer_name,'/home/pi/Desktop/template_test2.jpg',"PhotoBooth",{})
conn.printFile(printer_name,'/home/pi/Desktop/4up.jpg',"PhotoBooth",{})
