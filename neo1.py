from IO7FuPython import ConfiguredDevice
import json
import time
import uComMgr32
from machine import Pin
import neopixel

# NeoPixel 초기화 (8개 LED)
np = neopixel.NeoPixel(Pin(15), 8)

def setNeo(on):
    color = (255, 255, 255) if on else (0, 0, 0)
    for i in range(8):
        np[i] = color
    np.write()

def toggleNeo():
    current_on = np[0] != (0, 0, 0)
    setNeo(not current_on)

def handleCommand(topic, msg):
    global lastPub
    jo = json.loads(msg.decode())

    # {"d":{"neo":"toggle"}} 여길 그대로 읽는다
    if "neo" in jo.get("d", {}):
        cmd = jo["d"]["neo"]

        if cmd == "on":
            setNeo(True)
        elif cmd == "off":
            setNeo(False)
        elif cmd == "toggle":
            toggleNeo()

        # 즉시 상태 보고
        lastPub = time.ticks_ms() - device.meta['pubInterval']

# Wi-Fi + Device
nic = uComMgr32.startWiFi('valve')
device = ConfiguredDevice()
device.setUserCommand(handleCommand)
device.connect()

# 초기값
setNeo(False)
lastPub = time.ticks_ms() - device.meta['pubInterval']

# 메인 루프
while True:
    device.loop()   # 별도 reconnect 루프 없음

    # 주기적 status publish
    if (time.ticks_ms() - lastPub) > device.meta['pubInterval']:
        lastPub = time.ticks_ms()
        device.publishEvent(
            "status",
            json.dumps({
                "d": {
                    "neo": "on" if np[0] != (0, 0, 0) else "off"
                }
            })
        )

