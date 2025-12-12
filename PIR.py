from IO7FuPython import ConfiguredDevice
import json
import time
import uComMgr32
from machine import Pin
import ntptime
import gc 

# --- GPIO 핀 설정 ---
PIR_PIN = 15
pir_sensor = Pin(PIR_PIN, Pin.IN, Pin.PULL_DOWN)

# --- 통신 안정화 변수 ---
RECONNECT_DELAY_MS = 10000 
LAST_RECONNECT_TIME = 0
LAST_PUB_TIME = 0
PUB_INTERVAL = 1000 # 1초마다 상태 보고

# --- 함수 정의 ---
def sync_time():
    try:
        ntptime.settime()
        print(f"Time synchronized: {time.localtime()}")
        return True
    except Exception as e:
        print(f"NTP sync failed: {e}")
        return False

# --- 초기화 및 연결 ---
nic = uComMgr32.startWiFi('pir_sensor')
device = ConfiguredDevice()

if nic is not None:
    if sync_time():
        device.connect()
        print("IO7 Connected.")
    else:
        print("MQTTS initial connection failed.")
        
    # --- 메인 루프 ---
    while True:
        current_time = time.ticks_ms()
        
        # 1. 🚨 통신 재연결 로직 (10초 간격) 🚨
        if not device.loop():
            if current_time - LAST_RECONNECT_TIME > RECONNECT_DELAY_MS:
                LAST_RECONNECT_TIME = current_time
                if sync_time():
                    device.connect()
                
        # 2. 🧠 메모리 안정화 (GC) 🧠
        if current_time % 30000 < 1000:
            gc.collect()
            
        # 3. 🏃 상태 게시 로직
        if (current_time - LAST_PUB_TIME) > PUB_INTERVAL:
            LAST_PUB_TIME = current_time
            pir_state = 'on' if pir_sensor.value() else 'off'
            # 클라우드에 상태 게시 (key: pir_status)
            device.publishEvent('status', json.dumps({'d': {'pir_status': pir_state}}))
            
        time.sleep(0.01) # 짧은 딜레이

