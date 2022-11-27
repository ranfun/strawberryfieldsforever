#pinouts
# 1 26 E
# 2 19 D
# 3 13 DP
# 4 6 C
# 5 5 G
# 6 9 4
# 7 24 B
# 8 18 3
# 9 12 2
# 10 23 F
# 11 8 A
# 12 16 1

import sys, os
import RPi.GPIO as GPIO
import time
import random
#fpid = os.fork()
#if fpid!=0:

to_display = '0000' #master ip goes here

GPIO.setmode (GPIO.BCM)
GPIO.setwarnings(False)
display_list = [8,24,6,19,26,23,5] #
# display list ref: A, B, C, D, E, F, G
for pin in display_list:
    GPIO.setup(pin,GPIO.OUT) # set pins for each segement

# digits 1, 2, 3,4
set_digit = [16,12,18,9] 
for digit in set_digit:
    GPIO.setup(digit,GPIO.OUT) # set pins for digit selector

digit_dot = 13
# dot GPIO port
GPIO.setup(digit_dot, GPIO.OUT)
GPIO.setwarnings(True)

# A, B, C, D,E,F,G
arrSeg = [[0,0,0,0,0,0,1],\
[1,0,0,1,1,1,1],\
[0,0,1,0,0,1,0],\
[0,0,0,0,1,1,0],\
[1,0,0,1,1,0,0],\
[0,1,0,0,1,0,0],\
[0,1,0,0,0,0,0],\
[0,0,0,1,1,1,1],\
[0,0,0,0,0,0,0],\
[0,0,0,0,1,0,0]]

def split_num(to_display): # splits the given number string
# Splits variable 'to_display' string to a list of elements,
# so that each element is a simple str number or space, and set strains to number
# of digits given
# 
    arrToDisplay = list(to_display)
    if "," in arrToDisplay:
        arrToDisplay[arrToDisplay.index(',')] = ','
# index "," inlist and replace with "."
    if len(arrToDisplay) > 5:
        raise ValueError('Given Number is out of the range of display!')
# raise error if given number is more that for digits
    return arrToDisplay

def show_display(num): # num represents any number that splitTodisplay cleans up
# this function basically activates digits and the corresponding display
# segements according to the variable(num), and removes '.' from the variable
# if it finds one
# 
# handling floating numbers
    if len(num) > 4:
        for i in range(0,4):
            new_num = [x for x in num if x!='.'] # if '.' in num, replaces '.' with "
            sel_digit = [[1, 0, 0, 0],\
            [0, 1, 0, 0],\
            [0, 0, 1, 0],\
            [0, 0, 0, 1]]

        GPIO.output(set_digit,sel_digit[i])
        GPIO.output(display_list,arrSeg[int(new_num[i])])
        # activate decimal digit
        if num[i+1] == '.':
            GPIO.output(digit_dot,0)
        else:
            GPIO.output(digit_dot,1)
            time.sleep(.0001)
# integer number
    else:
        for i in range(0,4):
            sel_digit = [[1, 0, 0, 0],\
            [0, 1, 0, 0],\
            [0, 0, 1, 0],\
            [0, 0, 0, 1]]
            GPIO.output(set_digit,sel_digit[i])
            GPIO.output(display_list,arrSeg[int(num[i])])
            time.sleep(.0001)

while(1):
    show_display(split_num(to_display))