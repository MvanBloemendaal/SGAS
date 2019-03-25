######################################################
# Program ViCap.py                                   #
#                                                    #
# Program to capture camera image while showing      #
# live video                                         #
# Records the time of each frame being captured      #
#                                                    #
#                                                    #
# NOTES:                                             #
# - Version 1.0 is first version for beta testing    # 
# - Customized for Trappenberg system                #
# - expects configuration file named Vicap.Conf.txt  #
# - in directory that contains the executable file   #
# - set camera frame rate in config file             #
# - set measurement directory in config file         #
# - user should create data sub directory before use #
#                                                    #
#                                                    #
#                                                    #
######################################################

import sys

import cv2
import time

from tkinter import *
from tkinter.messagebox import *
from numpy import *
from datetime import datetime
import pickle, tkinter, sys
import configparser
from tkinter import filedialog, messagebox

root = tkinter.Tk()
root.geometry("720x576") 
root.title("Vicap") 

# Define initial directory for storing measurement data
dataDirectory = "C:\\"

# Define version below
Version = "Ready..."

# Define some globals

frameRate = 50        # Framerate of AVI video 
useOriginalFramerate = False
dirName = ""            # Name of directory that stores video
videoFileName = ""
v = IntVar()
v.set(0)

#Define first camera to be used
CameraNumber = 0
CameraName= "Now Using Camera " + str(CameraNumber + 1) 


def initialize():
        global dataDirectory, frameRate, useOriginalFramerate
        # Read global settings from config file
        try:
                config = configparser.ConfigParser()
                config.read('ViCap.Conf.txt')
                dataDirectory= str( config.get("Default","dataDirectory"))
                frameRate= int (config.get("Default","frameRate"))
                useOriginalFramerate= config.getboolean("Default", "useOriginalFrameRate")
        except:
                messagebox.showwarning("Info", "Problem reading configuration file")
                root.destroy()
                sys.exit(0)
                
 

def getFileName():
        global videoFileName
        videoFileName= entryBox.get()

        # Update message in the listbox
        message = "Video filename is: " + videoFileName
        listbox.insert(END,"")
        listbox.insert(END, message)
        root.update()

def disableButtons():
        # Routine disables control buttons to prevent
        # illegal button actions
        RB0.configure(state=DISABLED)
        RB1.configure(state=DISABLED)
        RB2.configure(state=DISABLED)
        RB3.configure(state=DISABLED)
        button1.configure(state= DISABLED)
        button2.configure(state= DISABLED)
        button3.configure(state= DISABLED)
        button5.configure(state= DISABLED)
        entryText.configure(state=DISABLED)
        entryBox.configure(state=DISABLED)
        b.configure(state= DISABLED)

def enableButtons():
        # Routine enables control buttons
        RB0.configure(state=NORMAL)
        RB1.configure(state=NORMAL)
        RB2.configure(state=NORMAL)
        RB3.configure(state=NORMAL)
        button1.configure(state= NORMAL)
        button2.configure(state= NORMAL)
        button3.configure(state= NORMAL)
        button5.configure(state= NORMAL)
        entryText.configure(state=NORMAL)
        entryBox.configure(state=NORMAL)
        b.configure(state= NORMAL)


def exitFromRoot():
	# Routine for intercepting close action by
	# pressing red window title bar x button on root window 
	messagebox.showinfo("Info", "Use Exit button to stop")


def Button1():
	# Routine to check if camera is up and running

	# Read setting of radio button  
	CameraNumber = v.get()
	CameraName= "Viewing Camera " + str(CameraNumber + 1) + " - <ESC> to stop" 

	# Update message in the listbox 
	message = "Viewing Camera "+ str(CameraNumber  + 1)
	listbox.insert(END,"")
	listbox.insert(END, message)
	

	# Block buttons for improper use
	disableButtons()
	root.update()

	# Capture video from camera
	capture = cv2.VideoCapture(CameraNumber)

	if capture.isOpened():
		# Show image until <ESC> key is hit
		while True:
			flag, img = capture.read()
			cv2.imshow(CameraName, img)
			if cv2.waitKeyEx(2) == 27:
				break
	else:
		messagebox.showwarning("Warning", "Camera " + str(CameraNumber + 1) + " not initialized!")
	capture.release()
	
	# Make buttons avialable again
	enableButtons()
	root.update()
	
	# Remove Video Window
	cv2.destroyWindow(CameraName)


def Button2():
	# Routine that captures the video from the selected camera


	CameraNumber = v.get()
	CameraName= "Recording Using Camera " + str(CameraNumber  + 1) + " - <ESC> to stop"
	
        # Update message in the listbox
	message = "Recording Video Camera "+ str(CameraNumber  + 1)
	listbox.insert(END,"")
	listbox.insert(END, message)
	root.update()
	
	# Capture video from camera
	capture = cv2.VideoCapture(CameraNumber)
	if capture.isOpened():

        # Define video window
		cv2.namedWindow(CameraName, cv2.WINDOW_AUTOSIZE)


		# Find size of the video image
		flag, img = capture.read()
		w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))  
		h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
		if useOriginalFramerate:
			frameRate = capture.get(cv2.CAP_PROP_FPS)

		# Check if there is a valid video file name
		if (videoFileName == ""):
			messagebox.showwarning("Info", "Name for video file missing")
		elif(dirName == ""):
			messagebox.showwarning("Info", "Name for storage directory missing")
		
		else:
			# Define name of file that contains timing data
			# Timing data in same directory as the video data
			videoID = videoFileName[:-3]
			f = open(dirName +"/"+ videoID + "Timing.txt","w")

			# Define video output
			videoWriter = cv2.VideoWriter(dirName + "/"+ videoFileName,	cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),	frameRate, (w, h), 1)

			t0 = datetime.now()

			# Prepare data capture
			FrameNumber = 1
			colorCode = button2.cget("bg")
			button2.configure(bg = "red")
			button2.configure(text = "Now recording")
			disableButtons()
			root.update()
		
			while True:
				# Routine blocks until image is received
				flag, img = capture.read()
				elapsedTime = datetime.now() - t0
				videoWriter.write(img)
				cv2.imshow(CameraName, img)

				# Check if the <ESC> key was hit to stop
				if cv2.waitKeyEx(2) == 27:
					break
		
				# Write video frame number and time to file 
				timestring = "Frame " +str(FrameNumber)+ ": " +str(elapsedTime)[5:-3] + " s\r\n"
				f.write(timestring)
				FrameNumber = FrameNumber + 1
			
			videoWriter.release()
		
			# Message for the user
			listbox.insert(END, "Recording completed")
			enableButtons()
			button2.configure(bg = colorCode)
			button2.configure(text = "Capture video")
			root.update()
		
			# Close file with timing data
			f.close()
		
	else:
		messagebox.showwarning("Warning", "Camera " + str(CameraNumber + 1) + " not initialized!")
	capture.release()
	
	
	# Remove Video Window
	cv2.destroyWindow(CameraName)


def Button3():
	global dirName
	dirName = filedialog.askdirectory(parent=root,initialdir=dataDirectory,title='Select a directory for storing data')
	
	# Update message in the listbox
	message = "Datafolder is: "+ dirName
	listbox.insert(END,"")
	listbox.insert(END, message)
	root.update()

	
def Button5():
	# This routine removes the GUI window
	listbox.insert(END,"")
	listbox.insert(END,"Exiting Vicap")
	root.destroy()


# Define buttons in textframe
textframe = Frame(root)
button1 = Button(textframe, text="Preview video",command = Button1)
button2 = Button(textframe, text="Capture video",command = Button2)
button3 = Button(textframe, text="Select data folder",command = Button3)
button5 = Button(textframe, text="Exit", command = Button5)


# Define empty spaces
empty1 = Label(textframe)
empty2 = Label (textframe)
empty3 = Label (textframe)
              
# Define radiobuttons to select camera
RB0 = Radiobutton(textframe, text="Camera 1", variable=v, value=0)
RB1 = Radiobutton(textframe, text="Camera 2", variable=v, value=1)
RB2 = Radiobutton(textframe, text="Camera 3", variable=v, value=2)
RB3 = Radiobutton(textframe, text="Camera 4", variable=v, value=3)

# Define scrollbar
scrollbar = Scrollbar(root, orient=VERTICAL)
scrollbar.pack( side = RIGHT, fill = Y )
listbox = Listbox(root, width = 60, yscrollcommand=scrollbar.set) 
scrollbar.configure(command=listbox.yview)
listbox.insert(END,Version)

# Set up entrybox for video filename
entryText = Label(textframe, anchor = W, text = "Enter Video Filename: ")
entryBox = Entry(textframe)
entryBox.insert(0,"<Identifier>.C5.avi")
b = Button(textframe, text="OK", width=20, command=getFileName)


# Pack Buttons in textframe
RB0.pack()
RB1.pack()
RB2.pack()
RB3.pack()
button1.pack(fill=X)
empty1.pack()
empty2.pack()
button3.pack(fill=X)
entryText.pack()
entryBox.pack()
b.pack()
empty3.pack()
button2.pack(fill=X)
button5.pack(fill=X)

# Pack bottons and listbox
textframe.pack(side=LEFT)
#entryframe.pack(side=RIGHT)
listbox.pack(side=RIGHT)

# Intercept closing the root window via the red x button
root.protocol("WM_DELETE_WINDOW", exitFromRoot)

initialize()
root.mainloop() 

