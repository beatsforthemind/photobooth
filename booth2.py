#!/usr/bin/python

#IMPORTS
import RPi.GPIO as gpio
import picamera
import pygame
import time
import sys
import os
import random

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

print('STARING SCRIPT')

#Reset GPIO
gpio.cleanup()
gpio.setwarnings(False)

#Initialise global variables
closeme = True #Loop control variable
timepulse = 999 #Pulse rate of LED
LEDon = False #LED flashing control
gpio.setmode(gpio.BCM) #Set GPIO to BCM layout
Numeral = "" #Numeral is the number display
Message = "" #Message is a fullscreen message
SmallMessage = "" #SmallMessage is a lower banner message
TotalImageCount = 1 #Counter for display and to monitor paper usage
PhotosPerCart = 18 #Selphy takes 16 - 18 sheets per tray
goprint = True #Flag for printing

print('GLOBAL VARIABLES READY')
print('INITIALIZING PYGAME')

#Initialise Pygame
pygame.mixer.pre_init(44100, -16, 1, 1024*3) #Pre_init music, plays faster
print('pygame mixer pre_init complete')

# Check which frame buffer drivers are available
# Start with fbcon since directfb hangs with composite output
drivers = ['fbcon', 'directfb', 'svgalib']
found = False
for driver in drivers:
	# Make sure that SDL_VIDEODRIVER is set
	if not os.getenv('SDL_VIDEODRIVER'):
		os.putenv('SDL_VIDEODRIVER', driver)
	try:
		pygame.display.init()
	except pygame.error:
		print ('Driver: {0} failed.'.format(driver))
		continue
	found = True
	break

pygame.init()
pygame.display.init()

size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
print ("Framebuffer size: %d x %d" % (size[0], size[1]))

#### # screen = pygame.display.set_mode((800,480),pygame.FULLSCREEN) #Full screen 640x480
# screen = pygame.display.set_mode(size, pygame.FULLSCREEN)

# SAFELY SET DISPLAY MODE
# Alarm for KeyboardInterrupt
class Alarm(Exception):
	pass
def alarm_handler(signum, frame):
	raise Alarm
signal(SIGALRM, alarm_handler)
alarm(3)

try:
	print('trying to set_mode for display')
	screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
	alarm(0)
except Alarm:
	print('set_mode error, interrupting')
	raise KeyboardInterrupt

pygame.display.update()
print('pygame display set_mode complete')

pygame.init() #Initialise pygame
pygame.mouse.set_visible(0)

background = pygame.Surface(screen.get_size()) #Create the background object
print('pygame get screen get_size complete')
background = background.convert() #Convert it to a background
print('pygame background convert complete')

print('PYGAME INITIALIZED')

#UpdateDisplay - Thread to update the display, neat generic procedure
def UpdateDisplay():
	print('Running UpdateDisplay function')
	#Init global variables from main thread
	global Numeral
	global Message
	global SmallMessage
	global TotalImageCount
	global screen
	global background
	global pygame

	SmallText = "NEW YEARS EVE" #Default small message text   
	if(TotalImageCount >= (PhotosPerCart - 2)): #Low paper warning at 2 images less
		SmallText = "Paper Running Low!"
	if(TotalImageCount >= PhotosPerCart): #Paper out warning when over photos per cart
		SmallMessage = "Replace Paper & Reboot Printer!"
		TotalImageCount = 0 
	background.fill(pygame.Color("black")) #Black background
	smallfont = pygame.font.Font(None, 50) #Small font for banner message
	SmallText = smallfont.render(SmallText,1, (255,255,255))
	background.blit(SmallText,(10,445)) #Write the small text
	SmallText = smallfont.render(`TotalImageCount`+" / "+`PhotosPerCart`,1, (255,255,255))
	background.blit(SmallText,(710,445)) #Write the image counter

	if(Message != ""): #If the big message exists write it
		font = pygame.font.Font(None, 180)
		text = font.render(Message, 1, (255,255,255))
		textpos = text.get_rect()
		textpos.centerx = background.get_rect().centerx
		textpos.centery = background.get_rect().centery
		background.blit(text, textpos)
	elif(Numeral != ""): #Else if the number exists display it
		font = pygame.font.Font(None, 800)
		text = font.render(Numeral, 1, (255,255,255))
		textpos = text.get_rect()
		textpos.centerx = background.get_rect().centerx
		textpos.centery = background.get_rect().centery
		background.blit(text, textpos)

	screen.blit(background, (0,0))
	# pygame.draw.rect(screen,pygame.Color("red"),(10,10,770,430),2) #Draw the red outer box
	pygame.display.flip()

	return

# CHROMA HELPER
def rgb_to_hsv(r, g, b):
	maxc = max(r, g, b)
	minc = min(r, g, b)
	v = maxc
	if minc == maxc:
		return 0.0, 0.0, v
	s = (maxc-minc) / maxc
	rc = (maxc-r) / (maxc-minc)
	gc = (maxc-g) / (maxc-minc)
	bc = (maxc-b) / (maxc-minc)
	if r == maxc:
		h = bc-gc
	elif g == maxc:
		h = 2.0+rc-bc
	else:
		h = 4.0+gc-rc
	h = (h/6.0) % 1.0
	return h, s, v

#Pulse Thread - Used to pulse the LED without slowing down the rest
def pulse(threadName, *args):
	print('Running Pulse function')
	# global gpio
	# gpio.setmode(gpio.BCM)
	# gpio.setup(17, gpio.OUT)
	# gpio.setup(17, gpio.OUT, pull_up_down=gpio.PUD_DOWN)

	#print timepulse
	# while closeme:
		# global LEDon
		#print LEDon

		# if timepulse == 999:
			# gpio.output(17, False)
			# LEDon = True
		# else:
			# if LEDon:
				# gpio.output(17, True)
				# time.sleep(timepulse)
				# LEDon = False
			# else:
				# gpio.output(17, False)
				# time.sleep(timepulse)
				# LEDon = True

#Main Thread
def main(threadName, *args):
	print('Running instance of Main thread')
	
	#Setup variables
	global gpio
	gpio.setmode(gpio.BCM)
	
	# gpio.setup(24, gpio.IN) #Button on Pin 24 Reprints last image
	# gpio.setup(24, gpio.IN, pull_up_down=gpio.PUD_DOWN)	
	# gpio.setup(22, gpio.IN) #Button on Pin 22 is the shutter
	gpio.setup(22, gpio.IN, pull_up_down=gpio.PUD_DOWN)
		
	# FLASH
	gpio.setup(18, gpio.OUT)
	gpio.output(18, gpio.HIGH)
	# gpio.output(18, True)	

	global closeme
	global timepulse
	global TotalImageCount
	global Numeral
	global SmallMessage
	global Message

	Message = "Loading..."
	UpdateDisplay()
	time.sleep(5) #5 second delay to allow USB to mount
	
	#Initialise the camera object
	camera = picamera.PiCamera()
	#Transparency allows pigame to shine through
	camera.preview_alpha = 120
	camera.vflip = False
	camera.hflip = True
	camera.rotation = 90
	camera.brightness = 45
	camera.exposure_compensation = 6
	camera.contrast = 8
	camera.resolution = (1280,720)
	#Start the preview
	camera.start_preview()

	Message = "USB Check..."
	UpdateDisplay()

	#Following is a check to see there is a USB mounted if not it loops with a USB message
	usbcheck = False
	rootdir = '/boothbin/'

	while not usbcheck:
		print('usbcheck is false and is checking')
		dirs = os.listdir( str(rootdir) )
		print('usbcheck dirs: ' + str(dirs))
		for file in dirs:
			folder = os.path.join(rootdir,file)
			print('usbcheck folder is ' + str(folder))
			# if not file == 'SETTINGS' and os.path.isdir(folder):
			# if not os.path.isdir(folder):
			if os.path.isdir(folder):
				print('this usbcheck folder exists')
				usbcheck = True
				imagedrive = os.path.join(rootdir, file)
				print('imagedrive is: ' + str(imagedrive))
				imagefolder = os.path.join(imagedrive, 'PhotoBooth')
				print('imagefolder is: '+ str(imagefolder))
				#If a photobooth folder on the usb doesn't exist create it
				if not os.path.isdir(imagefolder):
					print('creating imagefolder')
					os.makedirs(imagefolder)

	Message = "Initialise"
	UpdateDisplay()

	#Procedure checks if a numerical folder exists, if it does pick the next number
	#Each start gets a new folder i.e. /photobooth/1/ etc
	notfound = True
	folderno = 1
	while notfound:
		tmppath = os.path.join(imagefolder,`folderno`)
		if not os.path.isdir(tmppath):
			os.makedirs(tmppath)
			imagefolder = tmppath
			notfound = False
		else:
			folderno = folderno + 1

	imagecounter = 0

	Message = ""
	UpdateDisplay()

	print('near main loop')
	#Main loop
	while closeme:
		try:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					# closeme = True
					print('hold')
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						# closeme = True
						print('hold')
		except KeyboardInterrupt:
			# closeme = True
			print('hold')
		            
		#input_value is the shutter
		# input_value = gpio.input(22)
		input_value = gpio.input(22)
		print('input_value is: ' + str(input_value))
		#input_value2 is photo reprint
		# input_value2 = gpio.input(24)
		this_true = True
		this_false = False

		UpdateDisplay()

		#Load a beep music file
		# pygame.mixer.music.load('/home/pi/Desktop/Beep.mp3')
		#Reprint button has been pressed
		print('near reprint')
		# if this_false == True:
		if this_false == True:
			print('REPRINT')
			#If the temp image exists send it to the printer
			if os.path.isfile('/home/pi/Desktop/tempprint.jpg'):
				#Open a connection to cups
				conn = cups.Connection()
				#Get a list of printers
				printers = conn.getPrinters()
				#Select printer 0
				printer_name = printers.keys()[0]
				Message = "Re-Print..."
				UpdateDisplay()

				#Print the buffer file
				printqueuelength = len(conn.getJobs())

				if  printqueuelength > 1:
					Message = "PRINT ERROR"
					conn.enablePrinter(printer_name)
					UpdateDisplay()
				elif printqueuelength == 1:
					SmallMessage = "Print Queue Full!"
					UpdateDisplay()
					conn.enablePrinter(printer_name)
					conn.printFile(printer_name,'/home/pi/Desktop/tempprint.jpg',"PhotoBooth",{})
					time.sleep(20)
					Message = ""
				UpdateDisplay()

		#input_value is the shutter release
		print('near take images')
		# if input_value == False:
		if input_value == 1:
		# if True == True:
			print('TAKING IMAGES')
			
			#FLASH ON
                        # gpio.output(18, gpio.HIGH)                    
                        gpio.output(18, gpio.LOW)

			# ####################
			subimagecounter = 0
			#Increment the image number
			imagecounter = imagecounter + 1
			#play the beep
			# pygame.mixer.music.play(0)
			#Display the countdown number
			Numeral = "5"
			UpdateDisplay()
			#Flash the light at half second intervals
			timepulse = 0.5
			#1 second between beeps
			time.sleep(1)

			# pygame.mixer.music.play(0)
			Numeral = "4"
			UpdateDisplay()
			timepulse = 0.4
			time.sleep(1)

			#FLASH ON
                        # gpio.output(18, gpio.HIGH)                    
                        # gpio.output(18, gpio.LOW)
			
			# pygame.mixer.music.play(0)
			Numeral = "3"
			UpdateDisplay()
			timepulse = 0.3
			time.sleep(1)

			# pygame.mixer.music.play(0)
			Numeral = "2"
			UpdateDisplay()
			timepulse = 0.2
			time.sleep(1)

			# pygame.mixer.music.play(0)
			Numeral = "1"
			UpdateDisplay()
			timepulse = 0.1
			time.sleep(1)

			#Camera shutter sound
			# pygame.mixer.music.load('/home/pi/Desktop/camera.mp3')
			# pygame.mixer.music.play(0)
			Numeral = ""
			Message = "Smile!"
			UpdateDisplay()
			
			#Increment the subimage
			subimagecounter = subimagecounter + 1
			
			#Create the filename
			filename = 'image'
			filename += `imagecounter`
			filename += '_'
			filename += `subimagecounter`
			filename += '.jpg'

			#Capture the image
			camera.capture(os.path.join(imagefolder,filename))

			#Create an image object
			# im = PIL.Image.open(os.path.join(imagefolder,filename)).transpose(Image.FLIP_LEFT_RIGHT)
			im = PIL.Image.open(os.path.join(imagefolder,filename)).transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_90)

			#FLASH OFF
			# gpio.output(18, gpio.LOW)
			gpio.output(18, gpio.HIGH)

			########################################
			########## IMAGE TAKEN
      			
			Message = "Working..."
			UpdateDisplay()
			
			########################################

			#Load the background template
			# bgimage = PIL.Image.open("/home/pi/Desktop/template.jpg")
			# bgimage = PIL.Image.open("/home/pi/Desktop/template_test.jpg")			
			# bgimage = PIL.Image.open("/home/pi/Desktop/template_test2.jpg")
			# bgimage = PIL.Image.open("/home/pi/Desktop/chroma_bg.jpg")
			# bgimage = PIL.Image.open("/home/pi/Desktop/chroma_bg2.jpg")			
			
			RandNum = random.randint(1, 68)
			RandImg = 'img_'+str(RandNum)+'.jpg'
			RandPath = '/home/pi/Desktop/chroma/'+RandImg
			bgimage = PIL.Image.open(RandPath)			

			#Thumbnail the 4 images
			# im.thumbnail((560,400))
			# im2.thumbnail((560,400))
			# im3.thumbnail((560,400))
			# im4.thumbnail((560,400))
			
			# im.thumbnail((787,562))
			# im2.thumbnail((787,562))
			# im3.thumbnail((787,562))
			# im4.thumbnail((787,562))

			# im.thumbnail((1574,1124))
			# im2.thumbnail((1574,1124))
			# im3.thumbnail((1574,1124))
			# im4.thumbnail((1574,1124))

			#Paste the thumbnails to the background images
			# bgimage.paste(im,(15,20))
			# bgimage.paste(im2,(15,410))
			# bgimage.paste(im3,(15,820))
			# bgimage.paste(im4,(15,1230))
						
			imk = im.convert('RGBA')			
			
			# GREEN RANGES
			GREEN_RANGE_MIN_HSV = (100, 80, 70)
			GREEN_RANGE_MAX_HSV = (185, 255, 255)
			
			# Go through all pixels and turn each 'green' pixel to transparent
			pix = imk.load()
			width, height = imk.size
			for x in range(width):
				for y in range(height):
					r, g, b, a = pix[x, y]
					h_ratio, s_ratio, v_ratio = rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
					h, s, v = (h_ratio * 360, s_ratio * 255, v_ratio * 255)

					min_h, min_s, min_v = GREEN_RANGE_MIN_HSV
					max_h, max_s, max_v = GREEN_RANGE_MAX_HSV
					if min_h <= h <= max_h and min_s <= s <= max_s and min_v <= v <= max_v:
						pix[x, y] = (0, 0, 0, 0)
			
						
			# bgimage.paste(imk,(0,0),imk)
			bgimage.paste(imk,(0,0),imk)
			
			# bgimage.paste(im,(586,78))
			# bgimage.paste(im2,(586,867))
			# bgimage.paste(im3,(22,78))
			# bgimage.paste(im4,(22,867))

			#Two columns of 4
			# bgimage.paste(im,(620,20))
			# bgimage.paste(im2,(620,410))
			# bgimage.paste(im3,(620,820))
			# bgimage.paste(im4,(620,1230))
			
			#Create the final filename
			# Final_Image_Name = os.path.join(imagefolder,"Final_"+`imagecounter`+".jpg")
			#Save it to the usb drive
			bgimage.save(os.path.join(imagefolder,"Final_"+`imagecounter`+".jpg"))
			#Save a temp file, its faster to print from the pi than usb
			bgimage.save('/home/pi/Desktop/tempprint.jpg')

			#Connect to cups and select printer 0
			conn = cups.Connection()
			printers = conn.getPrinters()
			printer_name = printers.keys()[0]

			#Increment the large image counter
			TotalImageCount = TotalImageCount + 1
			Message = "Printing..."
			UpdateDisplay()
			#Print the file
			printqueuelength = len(conn.getJobs())
			#If multiple prints in the queue error
			if  printqueuelength > 1:
				Message = "ERROR"
				conn.enablePrinter(printer_name)
				UpdateDisplay()
			elif printqueuelength == 1:
				SmallMessage = "ERROR"
				conn.enablePrinter(printer_name)
				UpdateDisplay()

			time.sleep(2)
			conn.printFile(printer_name,'/home/pi/Desktop/tempprint.jpg',"PhotoBooth",{}) 
			# time.sleep(20)
			time.sleep(40)
			Message = ""
			UpdateDisplay()
			timepulse = 999
			#Reset the shutter switch
			while input_value == 1:
				input_value = gpio.input(22)
				# print('hold')
	#We are exiting so stop preview
	camera.stop_preview()

#Launch the main thread
print('Launching Main thread')
Thread(target=main, args=('Main',1)).start()

#Launch the pulse thread
print('Launching Pulse thread')
Thread(target=pulse, args=('Pulse',1)).start()

#sleep
time.sleep(5)
