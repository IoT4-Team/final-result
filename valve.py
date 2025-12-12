from IO7FuPython import ConfiguredDevice
import json
import time
import uComMgr32
from machine import Pin

relay_ac = Pin(16, Pin.OUT)
relay_heat = Pin(15, Pin.OUT)

relay_ac.value(0)
relay_heat.value(0)

def handleCommand(topic, msg):
    global lastPub
    
    try:
        payload_str = msg.decode('utf-8')
        
        if "{" in payload_str:
            jo = json.loads(payload_str)
            if 'd' in jo:
                payload = jo['d']
            else:
                payload = payload_str
        else:
            payload = payload_str
            
    except:
        payload = str(msg)
        
    if "AC_ON" in str(payload):
        relay_ac.value(1)
        print(">>> AC ON (GPIO 16)")
    elif "AC_OFF" in str(payload):
        relay_ac.value(0)
        print(">>> AC OFF")
        
    if "HEAT_ON" in str(payload):
        relay_heat.value(1)
        print(">>> HEAT ON (GPIO 15)")
    elif "HEAT_OFF" in str(payload):
        relay_heat.value(0)
        print(">>> HEAT OFF")

    lastPub = - device.meta['pubInterval']

nic = uComMgr32.startWiFi('valve2')
device = ConfiguredDevice()
device.setUserCommand(handleCommand)
device.connect()

TARGET_TOPIC = b"iot3/valve2/cmd/+/fmt/json"
device.client.subscribe(TARGET_TOPIC)
print(f">>> Ready. Topic: {TARGET_TOPIC}")

lastPub = time.ticks_ms() - device.meta['pubInterval']

while True:
    if not device.loop():
        break
        
    if (time.ticks_ms() - device.meta['pubInterval']) > lastPub:
        lastPub = time.ticks_ms()
        
        status_payload = {
            'd': {
                'ac': 'on' if relay_ac.value() else 'off',
                'heater': 'on' if relay_heat.value() else 'off'
            }
        }
        device.publishEvent('status', json.dumps(status_payload))
