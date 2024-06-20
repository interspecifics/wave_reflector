"""
Wave Reflector
--------------

micropython routine for testing speed on button motor.



1. erase and flash the firmware
----------------------------
download .bin from https://micropython.org/download/ESP32_GENERIC_S3/
python -m esptool --chip esp32s3 erase_flash
python -m esptool --chip esp32s3 --port COM4 --baud 460800 write_flash -z 0 D:/SK/PY/wave_reflect/ESP32_GENERIC_S3-20240602-v1.23.0.bin

2. 

"""

from machine import Pin, ADC, PWM, I2C
from time import sleep, time
from uosc.client import Bundle, Client, create_message
from neopixel import NeoPixel
import ssd1306
import math


# functions ------------------------------------------------
def gen_sin_wt(num_samples):
    wavetable = []
    for i in range(num_samples):
        angle = 2 * math.pi * i / num_samples
        wavetable.append(math.sin(angle))
    return wavetable

# ----------------------------------------------------------

# analog sensor
#pot = ADC(Pin(4))
#pot.atten(ADC.ATTN_11DB)       #Full range: 3.3v

# onboard pixel (not working)
pin_pix = Pin(48, Pin.OUT)
npx = NeoPixel(pin_pix, 1)
npx[0] = (0,0,0)
npx.write()
sleep(1)
npx[0] = (0,255,0)
npx.write()
sleep(1)


#button
pin_btn_a = Pin(8, Pin.IN)
btn_st_a = pin_btn_a.value()
pin_btn_b = Pin(9, Pin.IN)
btn_st_b = pin_btn_b.value()
mode = 0
past_mode = 0

# oled display on default 0x3C i2c addr
i2c = I2C(sda=Pin(4), scl=Pin(5))
display = ssd1306.SSD1306_I2C(128, 64, i2c)
# init the oled
display.fill(0)
display.text('<interspecifics>', 0, 0, 1)
display.show()


# power and limits of amplitud modulated signal
MAX_POWR = 2**16 - 1
pwm_powr_base = 2**15
pwm_freq = 1000
delta_powr = 32

signal = PWM(Pin(7), 10000, duty=0)
print(signal)


# generate a sin wavetable with 1000 steps
mode=0
len_arr = 100
wt = gen_sin_wt(len_arr)
wt = [0 for _ in range(len_arr)]
display.fill_rect(0, 10, 128, 64, 0)
display.text('mode: {}'.format(mode), 0, 24, 1)
display.text('wt.len: {}'.format(len_arr), 0, 36, 1)
display.show()

while True:
    btn_st_a = pin_btn_a.value()
    btn_st_b = pin_btn_b.value()
    #print (btn_st)
    if btn_st_a==0 or btn_st_b==0:
        sleep(2/10)
        if btn_st_a==0:
            mode += 1
            if mode>20: mode=0
        elif btn_st_b==0:
            mode -= 1
            if mode<0: mode=20
        # then select the freq/mode
        if mode==0:
            len_arr = 100
            wt = [0 for _ in range(len_arr)]
        elif mode==1:
            len_arr = 25
            wt = gen_sin_wt(len_arr)            
        elif mode==2:
            len_arr = 50
            wt = gen_sin_wt(len_arr)            
        elif mode==3:
            len_arr = 100
            wt = gen_sin_wt(len_arr)            
        elif mode==4:
            len_arr = 200
            wt = gen_sin_wt(len_arr)            
        elif mode==5:
            len_arr = 400
            wt = gen_sin_wt(len_arr)            
        elif mode==6:
            len_arr = 800
            wt = gen_sin_wt(len_arr)
        elif mode==7:
            len_arr = 1600
            wt = gen_sin_wt(len_arr)            
        elif mode==8:
            len_arr = 3200
            wt = gen_sin_wt(len_arr)
        elif mode==9:
            len_arr = 6400
            wt = gen_sin_wt(len_arr)
        elif mode==10:
            len_arr = 6400
            wt = [0 for _ in range(len_arr)]
        elif mode==11:
            len_arr = 6400
            wt = gen_sin_wt(len_arr)+[0 for _ in range(len_arr)]
        elif mode==12:
            len_arr = 6400
            wt = gen_sin_wt(len_arr)+[0 for _ in range(2*len_arr)]
        elif mode==13:
            len_arr = 6400
            wt = gen_sin_wt(len_arr)+[0 for _ in range(3*len_arr)]
        elif mode==14:
            len_arr = 6400
            wt = gen_sin_wt(len_arr)+[0 for _ in range(4*len_arr)]
        elif mode==15:
            len_arr = 6400
            wt = gen_sin_wt(len_arr)+[0 for _ in range(5*len_arr)]
        elif mode==16:
            len_arr = 3200
            wt = gen_sin_wt(len_arr)+[0 for _ in range(2*len_arr)]
        elif mode==17:
            len_arr = 3200
            wt = gen_sin_wt(len_arr)+[0 for _ in range(4*len_arr)]
        elif mode==18:
            len_arr = 3200
            wt = gen_sin_wt(len_arr)+[0 for _ in range(8*len_arr)]
        elif mode==19:
            len_arr = 3200
            wt = gen_sin_wt(len_arr)+[0 for _ in range(10*len_arr)]
        elif mode==20:
            len_arr = 3200
            wt = [0 for _ in range(len_arr)]
        # show info
        #display.fill(0)
        #display.text('<interspecifics>', 0, 0, 1)
        display.fill_rect(0, 10, 128, 64, 0)
        display.text('mode: {}'.format(mode), 0, 24, 1)
        display.text('wt.len: {}'.format(len_arr), 0, 36, 1)
        display.show()

    for i,s in enumerate(wt):
        if mode==0 or mode==10 or mode==20:
            signal.duty(s)
        elif mode>0 and mode<10:
            signal.duty(512 + math.floor(s * (256+128+64)))
        else:
            if i<len_arr:
                signal.duty(512 + math.floor(s * (256+128+64)))
            else:
                signal.duty(s)
        #print(signal)
        #signal.duty_u16(pwm_powr_base + math.floor(s * (pwm_powr_base-1)))
        #display.fill_rect(0, 12, 128, 32, 0)
        #display.text(str(signal.duty_u16()), 0, 12, 1)
        #display.show()