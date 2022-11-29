//live LED Matrix
import sys 
import RPi.GPIO as GPIO

columnDataPin = 20
rowDataPin = 21
latchPIN = 14
clockPIN = 15

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


GPIO.setmode(GPIO.BCM)
GPIO.setup((columnDataPin,rowDataPin,latchPIN,clockPIN),GPIO.OUT)

background=[["00000000"],["00000000"],["00000000"],["00000000"],["00000000"],["00000000"],["00000000"],["00000000"]]
ledmatrix_count = 0
sum_value_led_matrix = 0

while(1):
	sum_value_led_matrix = value_data[log_count] + sum_value_led_matrix	// value_data[log_count] is the light value
        ledmatrix_count = ledmatrix_count + 1
        if ledmatrix_count == 4: 						//update led matrix every 4 seconds
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
