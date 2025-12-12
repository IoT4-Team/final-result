from IO7FuPython import ConfiguredDevice
import json
import time
import uComMgr32
from machine import Pin

button = Pin(15, Pin.IN, Pin.PULL_UP)
state = 'released'  # 초기 상태
lastPub = 0
last_press = 0  # 디바운스용

def button_pressed(p):
    global state, lastPub, last_press
    now = time.ticks_ms()
    if time.ticks_diff(now, last_press) < 50:  # 50ms 디바운스
        return
    last_press = now

    if button.value():  # HIGH → 눌림
        state = 'pushed'
    else:  # LOW → 떼임
        state = 'released'
    lastPub = - device.meta['pubInterval']  # 바로 전송 가능



button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=button_pressed)

nic = uComMgr32.startWiFi('button')
device = ConfiguredDevice()
device.connect()

lastPub = time.ticks_ms() - device.meta['pubInterval']

while True:
    if not device.loop():
        break
    if (time.ticks_ms() - lastPub) > device.meta['pubInterval']:
        lastPub = time.ticks_ms()
        device.publishEvent('status', json.dumps({'d': {'button': state}}))

