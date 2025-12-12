from IO7FuPython import ConfiguredDevice
import json
import time
import uComMgr32
from machine import Pin, PWM
import ntptime
import gc 

# --- 설정값 ---
# 🚨🚨🚨 GPIO 핀 번호를 15번으로 설정합니다. 🚨🚨🚨
SERVO_PIN = 15      # 서보 모터 신호선 연결 GPIO 핀
FREQUENCY = 50      # 서보 표준 주파수 (50 Hz)
DUTY_CLOSED = 20    # 0도 (잠금 위치)
DUTY_OPEN = 100     # 180도 (잠금 해제 위치)
RECONNECT_DELAY_MS = 10000 

# --- 전역 변수 ---
servo = None
CURRENT_DOOR_STATE = "unknown" 
LAST_RECONNECT_TIME = 0
lastPub = 0 

# --- 함수 정의 ---
def sync_time():
    """NTP를 통해 시간을 동기화합니다."""
    try:
        print("Attempting NTP sync...")
        ntptime.settime()
        print(f"Time synchronized: {time.localtime()}")
        return True
    except Exception as e:
        # ... (NTP 실패 처리)
        return False

def publish_door_status():
    """현재 서보 상태를 클라우드에 전송합니다 (Heartbeat)."""
    global device, CURRENT_DOOR_STATE
    event_data = {"d": {"door_status": CURRENT_DOOR_STATE}}
    payload = json.dumps(event_data)
    try:
        device.publishEvent('status', payload)
    except Exception as e:
        # ... (상태 보고 실패 처리)
        pass

def set_servo_duty(duty_cycle):
    """서보 듀티 사이클 설정 및 구동 상태 출력"""
    global servo
    if servo is not None:
        try:
            servo.duty(duty_cycle)
            time.sleep_ms(300) 
            print(f"SERVO COMMAND SUCCESS: Duty set to {duty_cycle}")
            return True
        except Exception as e:
            print(f"SERVO COMMAND FAILED: {e}. Check Servo Power/Wiring.")
            return False
    return False

def close_door():
    """문 잠금 (서보 0도 위치)"""
    global CURRENT_DOOR_STATE
    if set_servo_duty(DUTY_CLOSED):
        CURRENT_DOOR_STATE = "closed"
        publish_door_status()
    
def open_door():
    """문 잠금 해제 (서보 180도 위치)"""
    global CURRENT_DOOR_STATE
    if set_servo_duty(DUTY_OPEN):
        CURRENT_DOOR_STATE = "open"
        publish_door_status()

def handleCommand(topic, msg):
    """클라우드 명령 수신 핸들러: door 명령을 받아 서보를 제어합니다."""
    print(f"COMMAND RECEIVED: Topic={topic}, Msg={msg}") 
    
    try:
        jo = json.loads(str(msg, 'utf8'))
    except:
        return

    if "door" in jo.get('d', {}):
        command = jo['d']['door']
        print(f"Parsed Command: {command}")
        if command == 'open':
            open_door()     
        elif command == 'close':
            close_door()
            
# --- 초기화 및 연결 ---
nic = uComMgr32.startWiFi('surbo1') 
device = ConfiguredDevice()
device.setUserCommand(handleCommand)

# Pin 객체를 먼저 생성하여 전역에 유지
servo_pin_obj = Pin(SERVO_PIN) 

if nic is not None:
    if sync_time():
        device.connect()
        print("IO7 Connected.")
        
        # 🚨 PWM 객체 초기화 (GPIO 15)
        try:
            servo = PWM(servo_pin_obj, freq=FREQUENCY) 
            close_door()
            
            lastPub = time.ticks_ms() - device.meta['pubInterval'] 
            
            print(f"Servo initialized successfully on GPIO {SERVO_PIN}.")
        except Exception as e:
            print(f"FATAL: Servo initialization failed: {e}. Check Pin/GPIO.")
            
    # --- 메인 루프 ---
    while True:
        current_time = time.ticks_ms()
        
        # 1. IO7 연결 유지 및 명령 수신
        if not device.loop():
            if current_time - LAST_RECONNECT_TIME > RECONNECT_DELAY_MS:
                LAST_RECONNECT_TIME = current_time
                if sync_time():
                    device.connect()
        
        # 2. 주기적 상태 보고 (Heartbeat)
        if (current_time - device.meta['pubInterval']) > lastPub:
            lastPub = current_time
            publish_door_status()
            
        # 3. 메모리 정리
        if current_time % 30000 < 1000:
            gc.collect()
            
        time.sleep_ms(50) 

# 프로그램 종료 시 PWM 비활성화
if servo is not None:
    servo.deinit()

