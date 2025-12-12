from IO7FuPython import ConfiguredDevice
import uComMgr32
from machine import Pin, PWM
import time
import json

# ==========================================
# 1. 설정 및 변수 초기화
# ==========================================
SERVO_PIN = 4
SPEED_DELAY = 0.03  # 속도 조절

servo = PWM(Pin(SERVO_PIN), freq=50)
    
current_angle = 0
target_angle = 0

# (배열 변수 cmd_history 삭제됨)

def update_servo(angle):
    duty = int(((angle / 180) * 97) + 26)
    servo.duty(duty)

update_servo(0)

# ==========================================
# 2. MQTT 명령 처리 (즉시 실행 모드)
# ==========================================
def handleCommand(topic, msg):
    global target_angle, lastPub
    
    try:
        jo = json.loads(str(msg,'utf8'))
        
        if "fan" in jo['d']:
            # 들어온 명령을 바로 변수에 저장
            cmd = jo['d']['fan'] 
            
            print(f"Received Command: {cmd}")

            # -----------------------------------------------
            # [수정됨] 배열/투표 없이 즉시 목표 각도 설정
            # -----------------------------------------------
            if cmd == 'on':
                target_angle = 90
                print("Target -> 90 (Open)")
            else:
                target_angle = 0
                print("Target -> 0 (Close)")
                
            # 상태 변경 시 즉시 보고를 위해 타이머 리셋
            lastPub = - device.meta['pubInterval']

    except Exception as e:
        print(f"Error: {e}")

# ==========================================
# 3. 메인 실행
# ==========================================
nic = uComMgr32.startWiFi('servo_motor')

if nic is not None:
    print("WiFi Connected.")
    device = ConfiguredDevice()
    device.setUserCommand(handleCommand)
    device.connect()
    print("MQTT Connected.")

    lastPub = time.ticks_ms()

    while True:
        if not device.loop():
            break
            
        # 모터 부드럽게 움직이기 (Slow Move Logic)
        # 명령은 즉시 받아도, 물리적인 이동은 여기서 부드럽게 처리됨
        if current_angle != target_angle:
            if current_angle < target_angle:
                current_angle += 1
            else:
                current_angle -= 1
            
            update_servo(current_angle)
            time.sleep(SPEED_DELAY) 
            
        # 상태 전송
        if (time.ticks_ms() - lastPub) > device.meta['pubInterval']:
            lastPub = time.ticks_ms()
            state = 'on' if current_angle > 45 else 'off'
            device.publishEvent('status', json.dumps({'d': {'fan': state}}))
            
        if current_angle == target_angle:
            time.sleep(0.01)

else:
    print("Connection Failed.")
