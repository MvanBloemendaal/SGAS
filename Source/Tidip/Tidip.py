##################################################################################
# Program Tidip.py                                                               #
#                                                                                #
# Program retrieve temporal-distance                                             #
# parameters from video recording and                                            #
# the corresponding DLT matrix.			                                         #
# NOTES:                                                                         #
#                                                                                #
# - Requires Tidip.Conf.txt file for global settings                             #
# - Conf file resides in application directory                                   #
# - Framerate should be set according to camera used for capture                 #
# - User should select videofile, program searches for corresponding DLTMatrix   #
# - Expects video and DLT matrix in the same datafolder                          #
# - Expects that filenames are <videoname>.Ci.avi and DLTMatrix.Ci.txt           #
# - where i = 0,1,2,3...9                                                        #
#                                                                                #
# CHANGELOG:                                                                     #
#                                                                                #
#  -27 nov 2014: Change with respect to version 1.0                              #
#   The lenght and position of the red measurement line can now be set           #
#   in the Tidip.Conf.txt file													 #
#  -13 mar 2019: Change with respect to version 1.0.1                            #
#	Implemented python 3 and opencv 4.0.0.21									 #
#                                                                                #
##################################################################################

import wmi
from tkinter.messagebox import showinfo
import sys

import cv2, copy

from tkinter import *
from numpy import *
import pickle, tkinter
import os.path
import configparser
from tkinter import filedialog

# Define windows that hold buttons and labels
root = tkinter.Tk()
root.geometry("600x400") 
root.title("Tidip: Position and time assessment software")

resultWindow = tkinter.Tk()
resultWindow.title("Time and Distance")

# Define title of window that shows the video
windowTitle = "Playing Video - <ESC> to stop"

# Define default measurement directory
MeasurementsDir= "C:\\"

# Define default time between two video frames in seconds
InterFrameInterval = 0.02

# Initialize DLT Matrix as 3 rows and 4 columns
DLTMatrix = zeros((3,4))

# Initialize names of files containing videoclip and the associated DLT matrix
VideoFileName = ""
DLTFileName = ""

# Global variables
# Number of vide0 frame being shown
frameNumber = 0
# Previous coordinates of mouse pointer in video frame 
lastu = 0
lastv = 0
# X coordinate of the measurement line in millimeters w.r.t. moving frame origin
# Initial position is in the origin 
posx = 0
posy = 0

# X coordinates [ in mm] of begin and end location of the red measurement line
xBegin = -400
xEnd = 400

# Initialize global image object
img = None
imageCopy = None

def initialize():
        global MeasurementsDir, frameRate
        global xBegin, xEnd
        # Read global settings from config file
        try:
                config = configparser.ConfigParser()
                config.read("Tidip.Conf.txt")
                MeasurementsDir = str( config.get("Default","dataDirectory"))
                frameRate = float (config.get("Default","frameRate"))
                xBegin = int(config.get("Default", "beginRedLine"))
                xEnd = int(config.get("Default", "endRedLine"))
        except:
                messagebox.showwarning("Info", "Problem reading configuration file")
                root.destroy()
                sys.exit(0)


def checkFileNames():
        # Routine checks if DLT and Video filenames are availble
        # If not, the routine displays a warning.
        # Returns error code zero if all is OK
        
        error = 0
        if (DLTFileName == ""):
                messagebox.showwarning("Warning","No DLT matrix found")
                error = 1
        if (VideoFileName == ""):
                messagebox.showwarning("Warning","No video file read")
                error = 2
        return error

def disableButtons():
        # Routine disables control buttons to prevent
        # illegal button actions
        button1.configure(state= DISABLED)
        button2.configure(state= DISABLED)
        button3.configure(state= DISABLED)
        button4.configure(state= DISABLED)

def enableButtons():
        # Routine enables control buttons
        button1.configure(state= NORMAL)
        button2.configure(state= NORMAL)
        button3.configure(state= NORMAL)
        button4.configure(state= NORMAL)

def exitFromRoot():
	# Routine for intercepting close action by
	# pressing red window title bar x button on root window 
	"dummy function"
	messagebox.showinfo("Info", "Use Exit button to stop")
	pass

def exitFromResultWindow():
	# Routine for intercepting close action by
	# pressing red window title bar x button on window
	# that displays time and distance
	"dummy function"
	messagebox.showinfo("Info", "Use Exit button in main window")
	pass

def button1():
	global VideoFileName, DLTFileName, DLTMatrix
	VideoFileName = ""
	DLTFileName = ""
	listbox.insert(END, "")
	VideoFileName = filedialog.askopenfilename(parent=root,defaultextension='.avi',initialdir= MeasurementsDir, title='Select video file')
	if (VideoFileName[-3:] == "avi") or (VideoFileName[-3:] == "AVI"):
		aviCamID = VideoFileName[-5]
		listbox.insert(END, "Video File Read")
		temp= VideoFileName.split("/")
		# Remove video file name to reconstruct absolute path of data folder
		temp = temp [0:-1]
		dirname= "/".join(temp)
		DLTFileName = dirname + "/" + "DLTMatrix.C" + aviCamID + ".txt"
		# Read DLT matrix from file, if possible
		if (DLTFileName != ""):
			if os.path.isfile(DLTFileName):
				file = open( DLTFileName )
				DLTMatrix = genfromtxt(file)
				file.close()
				listbox.insert(END, "Calibration Parameters Read")
			else:
				listbox.insert(END, "No DLT File Read")
				DLTFileName = ""
	else:
		listbox.insert(END, "No Video File Read")


def projectionOf(pointInSpace):
        # Function calculates the projection of the point in space,
        # described by the vector PointInSpace.
        # Projection is calculated using the DLT projection expression 
        # Definition PointInSpace is [x,y,z]
        # Units of coordinates are milimeters, if calibration was expressed
        # in milimeters
        
        x = pointInSpace[0]
        y = pointInSpace[1]
        z = pointInSpace[2]
        imageCoordinates = zeros(2)

        # Calculation of projection is below
        imageCoordinates[0] = DLTMatrix[0,0]*x + DLTMatrix[0,1]*y + DLTMatrix[0,2]*z + DLTMatrix[0,3]
        imageCoordinates[0] = imageCoordinates[0]/(DLTMatrix[2,0]*x + DLTMatrix[2,1]*y + DLTMatrix[2,2]*z + DLTMatrix[2,3])
        imageCoordinates[1] = DLTMatrix[1,0]*x + DLTMatrix[1,1]*y + DLTMatrix[1,2]*z + DLTMatrix[1,3]
        imageCoordinates[1] = imageCoordinates[1]/(DLTMatrix[2,0]*x + DLTMatrix[2,1]*y + DLTMatrix[2,2]*z + DLTMatrix[2,3])

        return imageCoordinates


def onMouseMove(event,x,y,flag,param):
        # Draws a cross in the z=0 plane to measure foot position
        # The line parallel to x-axis is used to measure the y coordinates on the floor
        # The line parallel to y-axis shows the measurement direction
        global posx, posy, lastu, lastv
        width = 1
        resolution = 1
        acceleration = 5

        if (event == cv2.EVENT_MOUSEMOVE):
                #w = frame.width
                #h = frame.height
                 #cv2.createImage((w,h),8,3)
                if (x > lastu):
                        posy = posy + resolution
                        if (flag == cv2.EVENT_FLAG_CTRLKEY):
                                posy = posy + (acceleration-1)*resolution
                if (x < lastu):
                        posy = posy - resolution
                        if (flag == cv2.EVENT_FLAG_CTRLKEY):
                                posy = posy - (acceleration-1)*resolution

                imageCopy = frame.copy()
                #cv2.copy(img,imageCopy)
                # This describes the line in the x-direction 
                point1 = [xBegin, posy,0]
                point2 = [xEnd, posy,0]
                # This describes the line in the y-direction
                point3 = [0, -200 + posy, 0]
                point4 = [0, 200 + posy, 0]
                marker1 = projectionOf(point1)
                marker2 = projectionOf(point2)
                marker3 = projectionOf(point3)
                marker4 = projectionOf(point4)

                p1x = int(marker1[0])
                p1y = int(marker1[1])
                p2x = int(marker2[0])
                p2y = int(marker2[1])
                p3x = int(marker3[0])
                p3y = int(marker3[1])
                p4x = int(marker4[0])
                p4y = int(marker4[1])
                # Note that the color order in cv.Line is Blue-Green-Red
                cv2.line(imageCopy,(p1x, p1y),(p2x, p2y),(0,0,255),width,8)
                cv2.line(imageCopy,(p3x, p3y),(p4x, p4y),(0,0,255),width,8)
                cv2.imshow(windowTitle, imageCopy)
                cv2.waitKey(1)
                lastu = x
                lastv = y

        if (event == cv2.EVENT_LBUTTONDOWN):
                position = str(posy)
                t = frameNumber * InterFrameInterval
                time = str(t)
                resultstring = "t =  " + time + " [s],  position = " + position + " [mm] " 
                outframe.configure(text = resultstring)
                outframe.update()


        if (event == cv2.EVENT_LBUTTONDOWN):
                position = str(posy)
                t = frameNumber * InterFrameInterval
                time = str(t)
                resultstring = "t =  " + time + " [s],  position = " + position + " [mm] " 
                outframe.configure(text = resultstring)
                outframe.update()


def button3():
	global frame, posx, posy, frameNumber
	# In this routine the user can go through the video record, and measure time and
	# position of the foot on the ground.


	# Initialize measurement line in the origin of coordinate system
	posx = 0
	posy = 0

	# Set width of lines
	width = 2

	# Set Parameters for drawing text
	font = cv2.FONT_HERSHEY_SIMPLEX

	# Check if selected video and DLT matrix are present
	errornumber = checkFileNames()
	if (errornumber !=0): return

	disableButtons()
	root.update()
	
	# Define video capture 
	capture = cv2.VideoCapture(VideoFileName)
	
        # Now go through loop to collect a number of frames        
	nFrames = int ( capture.get (cv2.CAP_PROP_FRAME_COUNT) )
	fps = capture.get( cv2.CAP_PROP_FPS )
	#fps = 25
	waitPerFrameInMilisec =  int (1/fps * 1000/1 )
	
	# Initialize on first video frame
	frameNumber = 0
	while (frameNumber < nFrames):
		# Get the frame to be processed
		capture.set(cv2.CAP_PROP_POS_FRAMES, frameNumber)
		# Show frame on the screen
		flag, frame = capture.read()
		cv2.imshow(windowTitle, frame)

		k = cv2.waitKeyEx(0)
		# Press Right Arrow key to proceed to next video frame
		if (k == 2555904):
			frameNumber += 1
		# Press Left Arrow key to go back one video frame
		if (k == 2424832):
			frameNumber += -1
			if frameNumber < 0: frameNumber = 0

		# Image is now frozen. Now control ruler to find the y coordinate of the foot 
		cv2.setMouseCallback(windowTitle, onMouseMove)

		# Terminate analysis by pressing <ESC>
		if (k==27): break

	capture.release()
	# Remove Video and Result Windows
	outframe.configure(text = "Time and Position Measurement Finished")
	cv2.destroyWindow(windowTitle)
	enableButtons()
	root.update()
	root.update()
	
	
def button4():
        # This routine removes the GUI window
        listbox.insert(END,"")
        listbox.insert(END,"Exiting Time Distance Analyzer")
        resultWindow.destroy()
        root.destroy()

def button2():
        # This routine draws origin, x, y and z axes of the
        # coordinate system
		
	# Check if selected video and DLT matrix are present
	errornumber = checkFileNames()
	if (errornumber !=0):
		listbox.insert(END, "")
		listbox.insert(END, "Cannot show coordinate system")
		return

	# First calculate the projection coordinates for the axes
	# Endpoint of axis is 500 milimeter from origin
	
	point = [0,0,0]
	projection = projectionOf(point)
	ou = int(projection[0])
	ov = int(projection[1])
	point = [500,0,0]
	projection = projectionOf(point)
	xu = int(projection[0])
	xv = int(projection[1])
	point = [0,500,0]
	projection = projectionOf(point)
	yu = int(projection[0])
	yv = int(projection[1])
	point = [0,0,500]
	projection = projectionOf(point)
	zu = int(projection[0])
	zv = int(projection[1])

	# Set width of axes
	width = 2

	# Set Parameters for drawing text
	font = cv2.FONT_HERSHEY_SIMPLEX

	# Prepare video viewing - block buttons to prevent user error
	disableButtons()
	root.update()
	
	# Start getting video frames from recording	
	capture = cv2.VideoCapture(VideoFileName)
	nFrames = int ( capture.get (cv2.CAP_PROP_FRAME_COUNT) )
	fps = capture.get( cv2.CAP_PROP_FPS )
	#fps = 25
	waitPerFrameInMilisec =  int (1/fps * 1000/1 )

        # Now go through loop to collect a number of frames
        # Color codes for the axis system
        # X-axis (R)ed
        # Y-axis (G)reen
        # Z-axis (B)lue
        # Note that the color order in cv.Line is Blue-Green-Red
	
	for f in range(nFrames):
        # Get the frame to be processed
		capture.set(cv2.CAP_PROP_POS_FRAMES, f)
		# Show frame on the screen
		flag, img = capture.read()
		# Draw Y axis in green
		cv2.line(img,(ou, ov),(yu, yv),(0,255,0),width,8)
		# Draw X axis in red
		cv2.line(img,(ou, ov),(xu, xv),(0,0,255),width,8)
		# Draw Z axis in blue
		cv2.line(img,(ou, ov),(zu, zv),(255,0,0),width,8)
		# Draw the legend
		cv2.putText(img,"x-axis",(10,30), font, 1, (0,0,255) )
		cv2.putText(img,"y-axis",(10,60), font, 1, (0,255,0) )
		cv2.putText(img,"z-axis",(10,90), font, 1, (255,0,0) )
		# Show frame on the screen
		cv2.imshow(windowTitle, img)
		k = cv2.waitKeyEx(waitPerFrameInMilisec)
		# Exit on pressing <ESC>
		if (k == 27) : break
		
	capture.release()

	# Unblock buttons
	enableButtons()
	root.update()
	# Remove Video Window
	cv2.destroyWindow(windowTitle)

# Define label to show time and distance
outframe = Label(resultWindow,height = 4, width = 40, text="Ready for Time and Position Measurement")
outframe.pack()
outframe.lift()

# Define buttons in textframe
textframe = Frame(root)
button1 = Button(textframe, text="Get Video Data",command = button1)
button2 = Button(textframe, text="Show World Coordinate System in Video", command = button2)
button3 = Button(textframe, text="Start Time - Distance Analysis",command = button3)
button4 = Button(textframe, text="Exit", command = button4)

# Define scrollbar
scrollbar = Scrollbar(root, orient=VERTICAL)
scrollbar.pack( side = RIGHT, fill = Y )
listbox = Listbox(root, width = 40, yscrollcommand=scrollbar.set) 
scrollbar.configure(command=listbox.yview)
listbox.insert(END,"Ready...")

button1.pack(fill=X)
button2.pack(fill=X)
button3.pack(fill=X)
button4.pack(fill=X)

# Pack bottons and listbox
textframe.pack(side=LEFT)
listbox.pack(side=RIGHT)

# Make sure that the smaller window is not hidden
resultWindow.wm_attributes("-topmost", 1)

# Intercept closing the root window via the red x button
root.protocol("WM_DELETE_WINDOW", exitFromRoot)
resultWindow.protocol("WM_DELETE_WINDOW", exitFromResultWindow)

initialize()
root.mainloop() 



