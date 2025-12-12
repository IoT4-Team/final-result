from IO7FuPython import ConfiguredDevice
import json
import time
import uComMgr32
from machine import Pin, ADC, Timer
import st7789
import tft_config
import vga2_8x16 as font1
import vga1_bold_16x32 as font2
import dht

sensor = dht.DHT22(Pin(16))

temperature = 0
humidity = 0
value = 71 

tft = tft_config.config(3, buffer_size=64*64*2)
tft.init()
tft.fill(st7789.BLACK)

tft.text(font2, 'Thermostat', 85, 5, st7789.WHITE)
tft.text(font1, 'Target      : ', 65, 50, st7789.WHITE)
tft.text(font1, 'Temperature : ', 65, 80, st7789.WHITE)
tft.text(font1, 'Humidity    : ', 65, 110, st7789.WHITE)

def r2t(r):
    return r * 0.1960784 + 10

def t2r(t):
    return (t - 10) / 0.1960784

lastMeasured = -2001

def measureData():
    global temperature, humidity, lastMeasured
    if (time.ticks_ms() - 2000) > lastMeasured:
        lastMeasured = time.ticks_ms()
        try:
            sensor.measure()
            temperature = sensor.temperature()
            humidity = sensor.humidity()
        except OSError as e:
            print("Sensor read failed:", e)
        
        display()

def display():
    tft.text(font1, f'{round(r2t(value),2)}', 200, 50, st7789.WHITE)
    tft.text(font1, f'{round(temperature, 2)}', 200, 80, st7789.WHITE)
    tft.text(font1, f'{round(humidity, 2)}', 200, 110, st7789.WHITE)

def handleCommand(topic, msg):
    global lastPub, value
    try:
        jo = json.loads(str(msg,'utf8'))
        
        if ("target" in jo['d']):
            value = t2r(int(jo['d']['target']))
            lastPub = - device.meta['pubInterval']
            display()
            print(f">>> Target updated: {jo['d']['target']}")
            
    except Exception as e:
        print(f"Command error: {e}")

nic = uComMgr32.startWiFi('io7ther
