import sys  
import time
import re
from netifaces import interfaces, ifaddresses, AF_INET
from socket import *
from gpiozero import LED, Button
from datetime import datetime
import matplotlib.pyplot as plt
import math
import linecache
import RPi.GPIO as GPIO

VERSIONNUMBER = 28
# packet type definitions
LIGHT_UPDATE_PACKET_To_SERVER = 1
DEFINE_SERVER_LOGGER_PACKET = 4
RESET_ESP = 2

MYPORT = 8118

SWARMSIZE = 5


button = Button(16)         # GPIO 16
led_yellow = LED(25)        # GPIO 25


def SendDEFINE_SERVER_LOGGER_PACKET(s):
        print ("DEFINE_SERVER_LOGGER_PACKET Sent") 
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

        # get IP address
        for ifaceName in interfaces():
            addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
            print ('%s: %s' % (ifaceName, ', '.join(addresses)))
        # last interface (wlan0) grabbed 
        print (addresses)
        myIP = addresses[0].split('.')
        print (myIP)
        data= ["" for i in range(8)]

        data[0] = str(DEFINE_SERVER_LOGGER_PACKET)
        data[1] = str(int(myIP[0])) # first octet of ip
        data[2] = str(int(myIP[1])) # second octet of ip
        data[3] = str(int(myIP[2])) # third octet of ip 
        data[4] = str(int(myIP[3])) # fourth octet of ip
        data[5] = str(0)
        data[6] = str(0)
        data[7] = str(0)
        
        print(' '.join(data).encode('utf-8'))
            
        s.sendto((' '.join(data).encode('utf-8')), ('<broadcast>', MYPORT))


def resetESP():
    print ("Reset all the ESP8266")
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    redata= ["" for i in range(8)]
    redata[0] = str(RESET_ESP)
    redata[1] = str(100)
    redata[2] = str(101)
    redata[3] = str(102)
    redata[4] = str(103) 
    redata[5] = str(104)
    redata[6] = str(105)
    redata[7] = str(106)
        
    print(' '.join(redata).encode('utf-8'))
            
    s.sendto((' '.join(redata).encode('utf-8')), ('<broadcast>', MYPORT))


def get_line_contxt(file_path, line_number):
    return linecache.getline(file_path,line_number).strip()

def shift_update_matrix(input_Col,Column_PIN,input_Row,Row_PIN,clock,latch):
  GPIO.output(clock,0)
  GPIO.output(latch,0)
  GPIO.output(clock,1)

  for i in range(7, -1, -1):
    GPIO.output(clock,0)
    GPIO.output(Column_PIN, int(input_Col[i]))
    GPIO.output(Row_PIN, int(input_Row[i]))
    GPIO.output(clock,1)

  GPIO.output(clock,0)
  GPIO.output(latch,1)
  GPIO.output(clock,1)

############################################################################
# set up sockets for UDP
s=socket(AF_INET, SOCK_DGRAM)
host = 'localhost';
s.bind(('',MYPORT))

print ("--------------")
print ("LightSwarm Logger")
print ("Version ", VERSIONNUMBER)
print ("--------------")


SendDEFINE_SERVER_LOGGER_PACKET(s)
time.sleep(3)
SendDEFINE_SERVER_LOGGER_PACKET(s)

log_count = 0

current_datetime = datetime.now()
str_current_datetime = str(current_datetime)
file_name = str_current_datetime + ".txt"
f = open(file_name, 'w')
f.write(str_current_datetime+ "\n")

device_data= ["" for i in range(30)]
value_data= ["" for i in range(30)]
device1 = 0
device2 = 0
device3 = 0
c = 0
one = 0
two = 0
three = 0
temp = 0
temp_totalvalue_1 = 0
temp_totalvalue_2 = 0
temp_totalvalue_3 = 0
xyz = 1


columnDataPin = 20
rowDataPin = 21
latchPIN = 14
clockPIN = 15

GPIO.setmode(GPIO.BCM)
GPIO.setup((columnDataPin,rowDataPin,latchPIN,clockPIN),GPIO.OUT)

background=[["00000000"],["00000000"],["00000000"],["00000000"],["00000000"],["00000000"],["00000000"],["00000000"]]
ledmatrix_count = 0
sum_value_led_matrix = 0

for x in range(8):
    RowSelect=[0,1,1,1,1,1,1,1]
    for i in range(0,8): # last value in rage is not included by default
      shift_update_matrix(''.join(map(str, RowSelect)),columnDataPin,''.join(map(str, background[i])),rowDataPin,clockPIN,latchPIN)
      RowSelect = RowSelect[-1:] + RowSelect[:-1]
    
    
while(1) :
    for x in range(8):
        RowSelect=[0,1,1,1,1,1,1,1]
        for i in range(0,8):
            shift_update_matrix(''.join(map(str, RowSelect)),columnDataPin,''.join(map(str, background[i])),rowDataPin,clockPIN,latchPIN)
            RowSelect = RowSelect[-1:] + RowSelect[:-1]
            
    d = s.recvfrom(1024)
        
    receive_data,client_address = s.recvfrom(1024)
    
    a = []
    a = re.findall("\d+\.?\d*",str(receive_data))
    a = list(map(int,a))
    
    packet_type = a[0]
    master_light_value = a[6]
    
    master_device_number = a[7]
    ip_1 = a[1]
    ip_2 = a[2]
    ip_3 = a[3]
    ip_4 = a[4]
    
    initialTime = time.time()
    
    for x in range(8):
        RowSelect=[0,1,1,1,1,1,1,1]
        for i in range(0,8):
            shift_update_matrix(''.join(map(str, RowSelect)),columnDataPin,''.join(map(str, background[i])),rowDataPin,clockPIN,latchPIN)
            RowSelect = RowSelect[-1:] + RowSelect[:-1]
    
    if (packet_type == 1):
        print("Device number: ", master_device_number)
        print("Light Value: ", master_light_value)
        f.write("Device IP: " + str(ip_1) +"." + str(ip_2) + "." + str(ip_3) +"." + str(ip_4) + "\n")
        f.write("Device ID: " + str(master_device_number) + "     Light Vlaue: " + str(master_light_value) + "\n")
        c = c + 1
        if master_device_number == 1:
            one = one + 1
            temp_totalvalue_1 = temp_totalvalue_1 + master_light_value
        if master_device_number == 2:
            two = two + 1
            temp_totalvalue_2 = temp_totalvalue_2 + master_light_value
        if master_device_number == 3:
            three = three + 1
            temp_totalvalue_3 = temp_totalvalue_3 + master_light_value
            
        for x in range(8):
            RowSelect=[0,1,1,1,1,1,1,1]
            for i in range(0,8):
                shift_update_matrix(''.join(map(str, RowSelect)),columnDataPin,''.join(map(str, background[i])),rowDataPin,clockPIN,latchPIN)
                RowSelect = RowSelect[-1:] + RowSelect[:-1]
                
        if c == 9:
            if one > two:
                if one > three:
                    temp = 1
            if two > one:
                if two > three:
                    temp = 2
            if three > one:
                if three > two:
                    temp = 3
            if temp == 1:
                device1 = device1 + 1
                device_data[log_count] = 1
                tt = temp_totalvalue_1 / one
                value_data[log_count] = int(tt)
            if temp == 2:
                device2 = device2 + 1
                device_data[log_count] = 2
                tt = temp_totalvalue_2 / two
                value_data[log_count] = int(tt)
            if temp == 3:
                device3 = device3 + 1
                device_data[log_count] = 3
                tt = temp_totalvalue_3 / three
                value_data[log_count] = int(tt)
                
            for x in range(8):
                RowSelect=[0,1,1,1,1,1,1,1]
                for i in range(0,8):
                    shift_update_matrix(''.join(map(str, RowSelect)),columnDataPin,''.join(map(str, background[i])),rowDataPin,clockPIN,latchPIN)
                    RowSelect = RowSelect[-1:] + RowSelect[:-1]
                
            sum_value_led_matrix = value_data[log_count] + sum_value_led_matrix
            ledmatrix_count = ledmatrix_count + 1
            if ledmatrix_count == 4:
                average_value_led_matrix = sum_value_led_matrix / 4
                ledmatrix_count = 0
                sum_value_led_matrix = 0
                if average_value_led_matrix < 129:
                    tmp = "00000001"
                if 128 < average_value_led_matrix and average_value_led_matrix < 257:
                    tmp = "00000010"
                if 256 < average_value_led_matrix and average_value_led_matrix < 385:
                    tmp = "00000100"
                if 384 < average_value_led_matrix and average_value_led_matrix < 513:
                    tmp = "00001000"
                if 512 < average_value_led_matrix and average_value_led_matrix < 641:
                    tmp = "00010000"
                if 640 < average_value_led_matrix and average_value_led_matrix < 769:
                    tmp = "00100000"
                if 768 < average_value_led_matrix and average_value_led_matrix < 897:
                    tmp = "01000000"
                if 896 < average_value_led_matrix:
                    tmp = "10000000"
                background.insert(0,tmp)
                background.pop(8)
                for x in range(8):
                        RowSelect=[0,1,1,1,1,1,1,1]
                        for i in range(0,8):
                            shift_update_matrix(''.join(map(str, RowSelect)),columnDataPin,''.join(map(str, background[i])),rowDataPin,clockPIN,latchPIN)
                            RowSelect = RowSelect[-1:] + RowSelect[:-1]
            log_count = log_count + 1
            if log_count == 30:
                log_count = 0
            c = 0
            one = 0
            two = 0
            three = 0
            temp = 0
            temp_totalvalue_1 = 0
            temp_totalvalue_2 = 0
            temp_totalvalue_3 = 0
            
            for x in range(8):
                RowSelect=[0,1,1,1,1,1,1,1]
                for i in range(0,8):
                    shift_update_matrix(''.join(map(str, RowSelect)),columnDataPin,''.join(map(str, background[i])),rowDataPin,clockPIN,latchPIN)
                    RowSelect = RowSelect[-1:] + RowSelect[:-1]
    
    if button.is_pressed:
        resetESP()
        led_yellow.on()
        time.sleep(3)
        led_yellow.off()
        resetESP()
        
        for x in range(8):
            RowSelect=[0,1,1,1,1,1,1,1]
            for i in range(0,8):
                shift_update_matrix(''.join(map(str, RowSelect)),columnDataPin,''.join(map(str, background[i])),rowDataPin,clockPIN,latchPIN)
                RowSelect = RowSelect[-1:] + RowSelect[:-1]

        f.write("Master time: " + "\n")
        f.write("Device 1 : " + str(device1) + "s" + "\n")
        f.write("Device 2 : " + str(device2) + "s" + "\n")
        f.write("Device 3 : " + str(device3) + "s" + "\n")
        f.close()
        device1 = 0
        device2 = 0
        device3 = 0
        
        file_30_name = "Last_30_secs_data.txt"
        f = open(file_30_name, 'w')
        for i in range(log_count, 30):
            f.write(str(device_data[i]) + "," + str(value_data[i]) + "\n")
        for i in range(0, log_count):
            f.write(str(device_data[i]) + "," + str(value_data[i]) + "\n")
        f.close()
        
        
        
        
        fig,axs = plt.subplots(2)
        bar_left = [1, 2, 3]
        a = 0
        b = 0
        c = 0
        a1 = ["" for i in range(30)]
        b1 = ["" for i in range(30)]
        c1 = ["" for i in range(30)]
        con = ["" for i in range(2)]
        con_1 = ["" for i in range(2)]
        con_2 = ["" for i in range(2)]
        bar_height_a = ["" for i in range(30)]
        bar_height_b = ["" for i in range(30)]
        bar_height_c = ["" for i in range(30)]
        file_path = r'/home/pi/Documents/216-hw4/Last_30_secs_data.txt'
        for line_number in range(log_count+1, 31):
            line = get_line_contxt(file_path, line_number)
            con = []
            con = re.findall("\d+\.?\d*",str(line))
            con = list(map(int,con))   #change string to list
            x = con[0]
            if x == 1:
                a = a + 1
            if x == 2:
                b = b + 1
            if x == 3:
                c = c + 1
            a1[line_number-1] = a
            b1[line_number-1] = b
            c1[line_number-1] = c
        for line_number in range(1, log_count+1):
            line = get_line_contxt(file_path, line_number)
            con_1 = []
            con_1 = re.findall("\d+\.?\d*",str(line))
            con_1 = list(map(int,con_1))   #change string to list
            x = con_1[0]
            if x == 1:
                a = a + 1
            if x == 2:
                b = b + 1
            if x == 3:
                c = c + 1
            a1[line_number-1] = a
            b1[line_number-1] = b
            c1[line_number-1] = c
        
        abc = log_count
        abc_1 = 0
        for i in range(30):
            if abc < 30:
                one_1 = a1[abc]
                two_1 = b1[abc]
                three_1 = c1[abc]
                bar_height_a[i] = one_1
                bar_height_b[i] = two_1
                bar_height_c[i] = three_1
                abc = abc + 1
            if abc == 30:
                if abc_1 < log_count:
                    one_2 = a1[abc_1]
                    two_2 = b1[abc_1]
                    three_2 = c1[abc_1]
                    bar_height_a[i] = one_2
                    bar_height_b[i] = two_2
                    bar_height_c[i] = three_2
                    abc_1 = abc_1 + 1
                
        #print(bar_height_a)
        #print(bar_height_b)
        #print(bar_height_c)
    
        y1, y2, y3= [], [], []
        

        file_path_1 = r'/home/pi/Documents/216-hw4/Last_30_secs_data.txt'
        y1_1 = []
        y2_1 = []

        temp = 0
        for line_number_1 in range(1, 31):
            line_1 = get_line_contxt(file_path_1, line_number_1)
            con_2 = []
            con_2 = re.findall("\d+\.?\d*",str(line_1))
            con_2 = list(map(int,con_2))   #change string to list
            x_1 = con_2[0]
            value_1 = con_2[1]
    
            y1_1.append(line_number_1)
            y2_1.append(value_1)
    
            if x_1 == 1:
                color_1 = 'red'
            if x_1 == 2:
                color_1 = 'green'
            if x_1 == 3:
                color_1 = 'blue'
        
            axs[1].set_xlabel('Time')
            axs[1].set_ylabel('Light Value')
            axs[1].set_title('Master Light Time')
    
            axs[1].plot([line_number_1-1,line_number_1], [temp,value_1], color = color_1)
            temp = value_1
            
            y1=bar_height_a[line_number_1-1]
            y2=bar_height_b[line_number_1-1]
            y3=bar_height_c[line_number_1-1]
            axs[0].bar(["Device 1", "Device 2", "Device 3"], [y1,y2,y3], color=['red', 'green', 'blue'])
            axs[0].set_ylim(0,31)
            axs[0].set_xlabel('Device #')
            axs[0].set_ylabel('Master Time - second')
            axs[0].set_title('Master Time For Each Deivce')
            
            plt.pause(1)
        plt.show()
        
        
        
        current_datetime = datetime.now()
        str_current_datetime = str(current_datetime)
        file_name = str_current_datetime + ".txt"
        f = open(file_name, 'w')
        f.write(str_current_datetime+ "\n")
        xyz = 1
        log_count = 0
        
        button.wait_for_press()
        SendDEFINE_SERVER_LOGGER_PACKET(s)
        time.sleep(3)
        SendDEFINE_SERVER_LOGGER_PACKET(s)
    
