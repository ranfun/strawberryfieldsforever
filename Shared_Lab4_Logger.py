'''
    LightSwarm Raspberry Pi Logger
    SwitchDoc Labs
'''
''' Lab 4 by Octavio Camacho Barragan
    This program is limited to work with up to 5 Swarm members due to the lab
    requirement of showing a unique color in the graphs for each Swarm Member
'''
#Thomas: LED Matrix
import sys
import time
import random
from netifaces import interfaces, ifaddresses, AF_INET
from socket import *

################# MY IMPORTS ###########
from gpiozero import LED, Button
import RPi.GPIO as GPIO
from threading import Thread, Lock
from copy import copy, deepcopy
from datetime import datetime
import logging
import matplotlib.pyplot as plt


VERSIONNUMBER = 6
# packet type definitions
LIGHT_UPDATE_PACKET = 0
RESET_SWARM_PACKET = 1
CHANGE_TEST_PACKET = 2   # Not Implemented
RESET_ME_PACKET = 3
DEFINE_SERVER_LOGGER_PACKET = 4
LOG_TO_SERVER_PACKET = 5
MASTER_CHANGE_PACKET = 6
BLINK_BRIGHT_LED = 7
# Maybe implement reset message here


MYPORT = 21135
SWARMSIZE = 5

logString = ""
# command from RasPiConnect Execution Code


############# MY VARIABLES ############
# The number of types of data for the masters_Info database
DATASIZE = 3  # 3 slots for the shape of my lists due to having IDs, total_Mastery_time, photo-resistor data
# The number of data points used for graphing
DATA_PNTS = 30  # 30 points for 30 seconds of graph info since we graph once a second

# Hardware Variables
button_gpio = 2     # Button connection is set at GPIO 2
yellowPin = 17      # Pins for LEDs

# Placeholders Variables initialized due to threads starting alongside prgram initialization
swarmID = -1
pVal = -1
previousFlashTime = 0
previousGraphTime = 0
ledState = False
flashTimeInterval = 3
graphTimeInterval = 1

# Main Database - A list holding lists structured like this: [ swarmID, total_Mastery_time, [pVal1,...,pValN] ]
# Where pVal stands for photo-resistor Value
masters_Info = [[0 for x  in range(DATASIZE)] for x in range(SWARMSIZE)]
for i in range(0,SWARMSIZE):
    masters_Info[i][2] = []

# Graph Database - A list holding lists structured like this: [swarmID, pVal]
# It's (DATASIZE - 1) because times don't need to be stored in graph_info
graph_info = [[None for x  in range(DATASIZE - 1)] for x in range(DATA_PNTS)]

# Control variables
start_logging = False
start_listening = False
run_assitant = False
old_Master = 'none'

# GPIO settings
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set pins as outputs
GPIO.setup(yellowPin,GPIO.OUT)
GPIO.setup(button_gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)

##################### Defining Functions  ###################
def completeCommand():
    f = open("/home/pi/LightSwarm/state/LSCommand.txt", "w")
    f.write("DONE")
    f.close()

def completeCommandWithValue(value):
    f = open("/home/pi/LightSwarm/state/LSResponse.txt", "w")
    f.write(value)
    print("in completeCommandWithValue=", value)
    f.close()
    completeCommand()

def processCommand(s):
    f = open("//home/pi/LightSwarm/state/LSCommand.txt", "r")
    command = f.read()
    f.close()
    if (command == "") or (command == "DONE"):
		# Nothing to do
        return False
    # Check for our commands
    #pclogging.log(pclogging.INFO, __name__, "Command %s Recieved" % command)
    print("Processing Command: ", command)
    if (command == "STATUS"):
        completeCommandWithValue(logString)
        return True
    if (command == "RESETSWARM"):
        SendRESET_SWARM_PACKET(s)		
        completeCommand()
        return True
	# check for , commands
    print("command=%s" % command)
    myCommandList = command.split(',')
    print("myCommandList=", myCommandList)
    # ------------------------------
    if (myCommandList.count > 1):
		# we have a list command
        if (myCommandList[0]== "BLINKLIGHT"):
            SendBLINK_BRIGHT_LED(s, int(myCommandList[1]), 1)
        if (myCommandList[0]== "RESETSELECTED"):
            SendRESET_ME_PACKET(s, int(myCommandList[1]))
        if (myCommandList[0]== "SENDSERVER"):
            SendDEFINE_SERVER_LOGGER_PACKET(s)
        completeCommand()
        return True
    completeCommand()
    return False


# UDP Commands and packets
def SendDEFINE_SERVER_LOGGER_PACKET(s):
    global myIP
    print("DEFINE_SERVER_LOGGER_PACKET Sent")
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    # get IP address
    for ifaceName in interfaces():
        addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
        print('%s: %s' % (ifaceName, ', '.join(addresses)))
    # last interface (wlan0) grabbed
    print(addresses)
    myIP = addresses[0].split('.')
    print(myIP)
    data= ["" for i in range(14)]
    #----------------------------------------
    data[0] = 0xF0
    data[1] = DEFINE_SERVER_LOGGER_PACKET
    data[2] = 0xFF # swarm id (FF means not part of swarm)
    data[3] = VERSIONNUMBER
    data[4] = int(myIP[0]) # first octet of ip
    data[5] = int(myIP[1]) # second octet of ip
    data[6] = int(myIP[2]) # third octet of ip
    data[7] = int(myIP[3]) # fourth octet of ip
    data[8] = 0x00
    data[9] = 0x00
    data[10] = 0x00
    data[11] = 0x00
    data[12] = 0x00
    data[13] = 0x0F
    #-------------------------
    s.sendto(bytearray(data), ('<broadcast>', MYPORT))

	
def SendRESET_SWARM_PACKET(s):
    print("RESET_SWARM_PACKET Sent")
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    #-----------------------
    data= ["" for i in range(14)]
    #-----------------------
    data[0] = 0xF0
    data[1] = RESET_SWARM_PACKET
    data[2] = 0xFF
    data[3] = VERSIONNUMBER
    data[4] = 0x00
    data[5] = 0x00
    data[6] = 0x00
    data[7] = 0x00
    data[8] = 0x00
    data[9] = 0x00
    data[10] = 0x00
    data[11] = 0x00
    data[12] = 0x00
    data[13] = 0x0F
    #-----------------------
    s.sendto(bytearray(data), ('<broadcast>', MYPORT))

def SendRESET_ME_PACKET(s, swarmID):
    print("RESET_ME_PACKET Sent")
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    #-----------------------
    data= ["" for i in range(14)]
    #-----------------------
    data[0] = 0xF0
    data[1] = RESET_ME_PACKET
    data[2] = swarmStatus[swarmID][5]
    data[3] = (VERSIONNUMBER)
    data[4] = 0x00
    data[5] = 0x00
    data[6] = 0x00
    data[7] = 0x00
    data[8] = 0x00
    data[9] = 0x00
    data[10] = 0x00
    data[11] = 0x00
    data[12] = 0x00
    data[13] = 0x0F
    #-----------------------
    s.sendto(bytearray(data), ('<broadcast>', MYPORT))


def SendCHANGE_TEST_PACKET(s, swarmID):
    print("RESET_ME_PACKET Sent")
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    #-----------------------
    data= ["" for i in range(14)]
    #-----------------------
    data[0] = 0xF0
    data[1] = RESET_ME_PACKET
    data[2] = swarmStatus[swarmID][5]
    data[3] = VERSIONNUMBER
    data[4] = 0x00
    data[5] = 0x00
    data[6] = 0x00
    data[7] = 0x00
    data[8] = 0x00
    data[9] = 0x00
    data[10] = 0x00
    data[11] = 0x00
    data[12] = 0x00
    data[13] = 0x0F
    #-----------------------      	
    s.sendto(bytearray(data), ('<broadcast>', MYPORT))
	

def SendBLINK_BRIGHT_LED(s, swarmID, seconds):
    print("BLINK_BRIGHT_LED Sent")
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    #-----------------------
    data= ["" for i in range(14)]
    #-----------------------
    data[0] = 0xF0
    data[1] = BLINK_BRIGHT_LED
    print("swarmStatus[swarmID][5]", swarmStatus[swarmID][5])
    data[2] = swarmStatus[swarmID][5]
    data[3] = VERSIONNUMBER
    if (seconds > 12.6):
        seconds = 12.6
    data[4] = int(seconds*10)
    data[5] = 0x00
    data[6] = 0x00
    data[7] = 0x00
    data[8] = 0x00
    data[9] = 0x00
    data[10] = 0x00
    data[11] = 0x00
    data[12] = 0x00
    data[13] = 0x0F
    #-----------------------      	
    s.sendto(bytearray(data), ('<broadcast>', MYPORT))


def parseLogPacket(message):
	incomingSwarmID = setAndReturnSwarmID(message[2])
	print("Log From SwarmID:", message[2])
	print("Swarm Software Version:", message[4])
    #-----------------------
	print("StringLength:", message[3])
	logString = ""
	for i in range(0, message[3] ):
		logString = logString + chr( message[i+5] )
    #-----------------------
	print("logString:", logString)
	return logString	

# build Webmap
def buildWebMapToFile(logString, swarmSize ):
    f = open("/home/pi/RasPiConnectServer/Templates/W-1a.txt", "w")
    webresponse = ""
    swarmList = logString.split("|")
    for i in range(0,swarmSize):
        swarmElement = swarmList[i].split(",")	
        print("swarmElement=", swarmElement)
        webresponse += "<figure>"
        webresponse += "<figcaption"
        webresponse += " style='position: absolute; top: "
        webresponse +=  str(100-20)
        webresponse +=  "px; left: " +str(20+120*i)+  "px;'/>\n"
        if (int(swarmElement[5]) == 0):
            webresponse += "&nbsp;&nbsp;&nbsp&nbsp;&nbsp;---"
        else:
            webresponse += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%s" % swarmElement[5]
        webresponse += "</figcaption>"
        webresponse += "<img src='" + "http://192.168.1.40:9750"
        #-----------------------
        if (swarmElement[4] == "PR"):
            if (swarmElement[1] == "1"):
                webresponse += "/static/On-Master.png' style='position: absolute; top: "
            else:
                webresponse += "/static/On-Slave.png' style='position: absolute; top: "
        else:
            if (swarmElement[4] == "TO"):
                webresponse += "/static/Off-TimeOut.png' style='position: absolute; top: "
            else:
                webresponse += "/static/Off-NotPresent.png' style='position: absolute; top: "
        webresponse +=  str(100)
        webresponse +=  "px; left: " +str(20+120*i)+  "px;'/>\n"
        webresponse += "<figcaption"
        webresponse += " style='position: absolute; top: "
        webresponse +=  str(100+100)
        webresponse +=  "px; left: " +str(20+120*i)+  "px;'/>\n"
        if (swarmElement[4] == "PR"):
            if (swarmElement[1] == "1"):
                webresponse += "&nbsp;&nbsp;&nbsp;&nbsp;Master"
            else:
                webresponse += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Slave"
        else:
            if (swarmElement[4] == "TO"):
                webresponse += "TimeOut"
            else:
                webresponse += "Not Present"
        webresponse += "</figcaption>"
        webresponse += "</figure>"
    #print webresponse
    f.write(webresponse)
    f.close()


def setAndReturnSwarmID(incomingID):
    for i in range(0,SWARMSIZE):
        if (swarmStatus[i][5] == incomingID):
            return i
        else:
            if (swarmStatus[i][5] == 0):  # not in the system, so put it in
                swarmStatus[i][5] = incomingID
                print("incomingID %d " % incomingID)
                print("assigned #%d" % i)
                return i
  	# if we get here, then we have a new swarm member.
  	# Delete the oldest swarm member and add the new one in
  	# (this will probably be the one that dropped out)
    oldTime = time.time()
    oldSwarmID = 0
    for i in range(0,SWARMSIZE):
        if (oldTime > swarmStatus[i][1]):
            oldTime = swarmStatus[i][1]
            oldSwarmID = i
	# remove the old one and put this one in....
    swarmStatus[oldSwarmID][5] = incomingID
 	# the rest will be filled in by Light Packet Receive
    print("oldSwarmID %i" % oldSwarmID)
    return oldSwarmID


# swarmStatus
swarmStatus = [[0 for x  in range(6)] for x in range(SWARMSIZE)]

# 6 items per swarm item

# 0 - NP  Not present, P = present, TO = time out
# 1 - timestamp of last LIGHT_UPDATE_PACKET received
# 2 - Master or slave status   M S
# 3 - Current Test Item - 0 - CC 1 - Lux 2 - Red 3 - Green  4 - Blue
# 4 - Current Test Direction  0 >=   1 <=
# 5 - IP Address of Swarm


for i in range(0,SWARMSIZE):
	swarmStatus[i][0] = "NP"
	swarmStatus[i][5] = 0


########## My Functions ###########
# Function that extracts the pValue from the log sent by the master
def pValFromLog(message):      # function used only with Masters sending a log!!!
    print("Log From SwarmID:", message[2])
    print("Swarm Software Version:", message[4])
    print("StringLength:", message[3])

    logString = ""
    for i in range(0, message[3] ):     # get the number of characters in message[3] into a string
        logString = logString + chr( message[i+5] ) # when you skip 5 you start looking into the part of the message where the ESP saved a log string
    print("logString:", logString)

    #print("i: ", i)
    #print("message type is: ", type(message))

    swarmList = logString.split("|")    # this split gives a list of information from each swarm member
    i = 0                               # sender will always be the first one in its log, so i = 0
    swarmElement = swarmList[i].split(",")  # this splits into a list the info logged for first swarm member (current Master)
    return int(swarmElement[3])     # fourth index in SwarmElement contains pValue


# Function to turn off the yellow LED
def turnLEDsOff():
    GPIO.output(yellowPin, GPIO.LOW)


# Function that records data to the log file
def saveLog():
    global masters_Info
    global graph_info
    global myIP
    global old_Master

    string1 = ''
    string2 = ''
    string3 = ''

    # Save current log file (if any) and start a new logfile
    logname = datetime.now().strftime('logFile_%Y_%m_%d-%H:%M:%S.log') # format is Year_Month_Day-Hours:Minutes:Seconds

    #Clearing out logging handlers so each time button is pressed a new file is created
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Configuring logging for 'matplotlib' module so it doesn't mess with the file logger
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    # Create and configure logger (using seconds also), otherwise
    # a button press within the same minute overwrites previous file
    # created within the same minute
    logging.basicConfig(filename=logname, format='%(message)s', filemode='w', level=logging.DEBUG)

    # Creating an object with the above config so I can use it in my logger calls
    logger = logging.getLogger()

    ''' Carry out the logging of the information '''
    logger.info("The Masters were:")
    # Build string for devices that were Masters
    for i in range(0,SWARMSIZE):
        if (masters_Info[i][0] != 0):  # ID is non-zero, so get ID and time per Master
            # Build the strings to be logged
            string1 = string1 + '.'.join(myIP[0:3]) + '.' + str(masters_Info[i][0]) + ', '
            string2 = string2 + 'For ' + '.'.join(myIP[0:3]) + '.' + str(masters_Info[i][0]) + ' time was: ' + str(masters_Info[i][1]) + '|'
            strPvals = [str(x) for x in masters_Info[i][2]]
            string3 = string3 + '.'.join(myIP[0:3]) + '.' + str(masters_Info[i][0]) + ',' + ','.join(strPvals) + '|'''

    # Log to file the IP addresses of Masters
    logger.info(string1.rstrip(", "))

    # Log to file the total times as Master of Masters
    string_list = string2.split("|")     # Get each time string in a list
    for i in range(len(string_list)):
        logger.info(string_list[i])      # Log each element in the list

    # Log to file the photo-resistor values of Masters
    logger.info("Raw Data:")
    string_list = string3.split("|")     # Get each pValue string in a list
    for i in range(len(string_list)):
        logger.info(string_list[i])      # Log each element in the list


    # Reset Lists and other variables
    # As a new log file will begin next time this function is called
    # So the history of Masters stored in masters_Info must be reset
    for i in range(SWARMSIZE):
        for j in range(DATASIZE - 1): # reset all data to 0 except for sublist in masters_Info[i][2]
            masters_Info[i][j] = 0
        masters_Info[i][DATASIZE - 1] = [] # Resetting sublist component of elements to empty list
    # Reset history in graph_info
    graph_info = [[None for x  in range(DATASIZE - 1)] for x in range(DATA_PNTS)]
    # Reset this variable
    old_Master = 'none'


# Function in thread to make LED stay on for 3 seconds after a button press
# As a thread, this functions runs from the beginning, non-stop
def blink_LED():
    global ledState
    global yellowPin
    global previousFlashTime
    global flashTimeInterval

    while(True):
        # Perform 3 seconds LED flash if button was pressed
        #print("before LED, ledState =", ledState)
        if (ledState):                                                  # This variable will be True after a button press
            GPIO.output(yellowPin, ledState)                            # Turn LED ON
            currentTime = time.perf_counter()                           # Grab current time to compare it to las time LED was set to ON
            if (currentTime - previousFlashTime) >= flashTimeInterval:  # Check if 3 seconds have passed since last time LED was set to ON
                ledState = False                                        # This if block is only entered when the button is pressed
                GPIO.output(yellowPin, ledState)                           # If 3 seconds have passed, turn off LED

# Function in thread to save info into databases used for logging and graphing
def save_graph():
    global logString
    global masters_Info
    global previousGraphTime
    global run_assitant
    global message
    global current_Master_time
    global pVal
    global graph_swarmID

    while (True):
        if (run_assitant):
            ''' Display graph '''
            # Grapgh the 2 plots
            #time_pre_graph = time.perf_counter()
            graph(graph_swarmID, pVal)
            #time_post_graph = time.perf_counter()
            #print("Time graphing:", (time_post_graph - time_pre_graph) )
            run_assitant = False

# Saves to the database which swarm members have become Masters since last button press
def setAndReturnMastersIndexAndID(ID):
    global masters_Info

    # If previously Master, continue, otherwise add as new Master
    for i in range(0,SWARMSIZE):
        if (masters_Info[i][0] == ID):
            return i, ID
        else:
            if (masters_Info[i][0] == 0):  # not in list, so put it in
                masters_Info[i][0] = ID
                #print('atsetandreturn', masters_Info)
                return i, ID


# Gets a database index and determines whether it belongs to a new or previous Master
# Returns True if the index of new_Master belongs to a new Master
# It also saves the time so far as Master for the old_Master
def new_master(new_Master):     # a member index in the masters_Info array
    global masters_Info
    global old_Master           # a member index in the masters_Info array
    global current_Master_time

    # I'm always saving the time of the old Master, whether it got replaced or not
    if (old_Master == 'none'):  # this is first Master in program/log, so return True
        old_Master = new_Master # and make old_Master become new_Master
        return True

    elif(old_Master == new_Master): # Master hasn't changed, return False
        # Add up the time old Master is still master
        masters_Info[old_Master][1] = masters_Info[old_Master][1] + (time.perf_counter() - current_Master_time)
        # Update current_Master_time, otherwise the added time gets skewed
        current_Master_time = time.perf_counter()
        return False

    elif (new_Master != old_Master):   # if new master, save time so far as Master for old Master
        # Add up the time old_Master was master
        masters_Info[old_Master][1] = masters_Info[old_Master][1] + (time.perf_counter() - current_Master_time)
        old_Master = new_Master     # change old_Master
        return True


# Builds and displays the graphs, one Bar Chart, and one Trace Chart
def graph(swarmID, pVal):
    ''' MISSING DETAIL ABOUT BAR GRAPH ONLY SHOWING LAST 30 SECONDS!!!!'''
    global myIP
    global masters_Info
    global graph_info
    num_of_Masters = 0
    IDs_list = []           # List where the full IP address of members will be stored
    times_list = []         # List where the total time of the current run is stored

    ''' THIS LIMITS PROGRAM FUNCTIONALITY TO 5 ESPs '''
    list_of_colors = ['red', 'green', 'blue', 'yellow', 'black']

    ''' Get graph info '''
    # Get x-coordinates, heights of bars (time) and labes for bars
    for i in range(0,SWARMSIZE):
        if (masters_Info[i][0] != 0):  # ID is non-zero, so count masters and save their IDs to a list
            num_of_Masters = num_of_Masters + 1
            # y-coordinates/heights of bars (time)
            times_list.append(masters_Info[i][1])
            # labels for bars
            IDs_list.append( '.'.join(myIP[0:3]) + '.' + str(masters_Info[i][0]) )

    #print("swarmID: ", swarmID)
    #print("pVal in graph: ", pVal)
    #print("graph_info: ", graph_info)
    #print("# of masters: ", num_of_Masters)
    #print("masters_Info: ", masters_Info)

    # Populate graph_info in reverse order, from the end to the beginning
    graph_info.pop(0)      # pop element at leftmost of list (oldest element)
    graph_info.append([ swarmID, pVal ])    # Append info received at the end of the list


    # bar graph x-coordinates
    x_bar_coors = list(range(1, num_of_Masters + 1, +1))    # i.e. with 3 ESPs the result is: [1,2,3]

    # trace graph x-coordinates
    x_trace_coors = list(range(31))
    x_trace_coors.pop(0)    # pop first element since X axis ends at 1 and begins at 30
    x_trace_coors.reverse() # The above comment explains why the list is reversed


    # Placing graphs in window
    plt_bar = plt.subplot2grid( (6,6), (0,0), rowspan=2, colspan=4 )
    plt_trace = plt.subplot2grid( (6,6), (3,0), rowspan=4, colspan=6 )


    # Name the bar graph axes and title
    plt_bar.set_xlabel('Swarm Member')
    plt_bar.set_ylabel('Time')
    plt_bar.set_title('Time as Master')

    # Name the trace graph axes and title
    plt_trace.set_xlabel('Number of seconds ago')
    plt_trace.set_ylabel('Photo-resistor Value')
    plt_trace.set_title('Sensor Readings')
    
    # Plot bar chart
    plt_bar.bar(x_bar_coors, times_list, tick_label = IDs_list, width = 0.8, color = list_of_colors[0:num_of_Masters])


    # Plotting a trace chart
    y_trace_coors = []
    for i,j in list( enumerate(graph_info)):
        y_trace_coors.append(graph_info[i][1])
    # Plot 29 lines (number of lines between all 30 data points)
    for i,j in list( enumerate(graph_info)):
        if i < (DATA_PNTS - 1):           # i goes from 0 to 29 for the 30 elements in graph_info
            for k in range(0, num_of_Masters):              # 'k' gets a index value that corresponds to an element index in the database masters_Info
                if graph_info[i][0] == masters_Info[k][0]:  # Check 'k' is the masters_Info element that matches the swarmID of the graph_info data point to be graphed
                    plt_trace.plot( [ x_trace_coors[i], x_trace_coors[i+1] ], [ y_trace_coors[i], y_trace_coors[i+1] ], color = list_of_colors[k] )


    # This so the Trace graph is set at the range between 30 and 1 secs ago
    plt_trace.set_xlim([DATA_PNTS,1])

    # Pack the plots and display them
    plt.tight_layout()
    plt.draw()
    plt.pause(0.001)



# Thread for having the LED be on for 3 seconds after a button press
thread1 = Thread(target=blink_LED)
thread1.start()
# Thread for having the info for graph and log saved without slowing down the reading of UDP messages
thread2 = Thread(target=save_graph)
thread2.start()


turnLEDsOff()

def button_pressed_callback(channel):
    global start_logging
    global ledState
    global previousFlashTime
    global run_assitant

    if start_logging == True:
        SendRESET_SWARM_PACKET(s)
        run_assitant = False
        #time_pre_svlg = time.perf_counter()
        saveLog()
        #time_post_svlg = time.perf_counter()
        #print("Time logging:", (time_post_svlg - time_pre_svlg) )


    print("Button pressed!")
    start_logging = True
    turnLEDsOff()

    # Variables set for the LED to be set to ON for 3 seconds on button press
    ledState = True                         # set LED boolean for the 3 seconds LED blink
    previousFlashTime = time.perf_counter() # Save time for the 3 seconds LED time interval check


GPIO.add_event_detect(button_gpio, GPIO.FALLING, callback=button_pressed_callback, bouncetime=1000)
# Bouncetime ensures callback is triggered once in 1 seconds
# The reason for 1 second is because the file names hold the time. Meaning that
# allowing for logging more than once a second erases the previous log


############## Main Program Loop ##########
#try:
print("Press button to connect and begin program")
while(True):
    if (start_logging):
        # Initial program setup
        print("--------------")
        print("LightSwarm Logger")
        print("Version ", VERSIONNUMBER)
        print("--------------")

        # set up socket for UDP
        s=socket(AF_INET, SOCK_DGRAM)
        s.bind(('',MYPORT))     # Bind RPi to port so it begins listening
        #print("IP Address: " + s.gethostbyname(s.gethostname())  )

        # first send out DEFINE_SERVER_LOGGER_PACKET to tell swarm where to send logging information
        SendDEFINE_SERVER_LOGGER_PACKET(s)
        time.sleep(3)
        SendDEFINE_SERVER_LOGGER_PACKET(s)

        start_listening = True


    while(start_listening) :  # In this while loop we catch broadcasted messages repeatedly
        d = s.recvfrom(1024)        # remember that this is blocking!
        message = d[0]
        addr = d[1]
        if ( len(message) == 8 or len(message) == 14 ):
            if (message[1] == LIGHT_UPDATE_PACKET):
                #print("GOT THE LIGHT_UPDATE_PACKET FROM ESP!")   # <-- mine to test
                incomingSwarmID = setAndReturnSwarmID(message[2])
                swarmStatus[incomingSwarmID][0] = "P"
                swarmStatus[incomingSwarmID][1] = time.time()

            if (message[1] == RESET_SWARM_PACKET):
                print("Swarm RESET_SWARM_PACKET Received")
                print("received from addr:",addr)

            if (message[1] == CHANGE_TEST_PACKET):
                print("Swarm CHANGE_TEST_PACKET Received")
                print("received from addr:",addr)

            if (message[1] == RESET_ME_PACKET):
                print("Swarm RESET_ME_PACKET Received")
                print("received from addr:",addr)

            if (message[1] == DEFINE_SERVER_LOGGER_PACKET):
                print("Swarm DEFINE_SERVER_LOGGER_PACKET Received")
                print("received from addr:",addr)

            if (message[1] == MASTER_CHANGE_PACKET):
                print("Swarm MASTER_CHANGE_PACKET Received")
                print("received from addr:",addr)
                for i in range(0,14):
                    print("ls["+str(i)+"]="+format(ord(message[i]), "#04x"))
        else:
            if (message[1] == LOG_TO_SERVER_PACKET):#<--- removed ord() surrounding message[1], since recvfrom() returns bytes, not strings in Python 3
                print("Swarm LOG_TO_SERVER_PACKET Received")
                # process the Log Packet
                #logString = parseLogPacket(message)
                #buildWebMapToFile(logString, SWARMSIZE )

                '''Save info for log '''
                # acquire info from message to get values into log database
                index, graph_swarmID = setAndReturnMastersIndexAndID(message[2]) # Save Master's ID info to database if it is new and store its index
                #time_pre_ext = time.perf_counter()
                pVal = pValFromLog(message)             # Get the sensor value from log string
                #time_post_ext = time.perf_counter()
                #print("Time extracting:", (time_post_ext - time_pre_ext) )

                # Saving pVal for log
                masters_Info[index][2].append(pVal)   # Append the value to the values list of the respective Master
                # Saving time as Master for log
                if (new_master(index)):  #<-- did master change?
                    current_Master_time = time.perf_counter() # get start time of new master

                currentTime = time.perf_counter()       # Save current time to compare it to time of last graph
                # At first this if is always entered since previousGraphTime starts at 0
                if (currentTime - previousGraphTime) >= graphTimeInterval: # if graphTimeInterval seconds have passed since last graph
                    #print("Graph every:", currentTime - previousGraphTime)
                    previousGraphTime = currentTime     # Save last time a graph was drawn
                    # Boolean variable for save_graph assitant thread to run and
                    # get the correct 'logString' and 'message' value every second
                    run_assitant = True
                # Without the use of a thread, the graphing of data
                # makes it so the main program ends up with a backlog of UDP
                # messages to which it needs to catch up. Making the graph charts
                # take several seconds to update to the most recent info

            else:
                print("error message length = ",len(message))

        processCommand(s)
