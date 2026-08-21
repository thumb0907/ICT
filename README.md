# ICT Mobile Platform Remote Control

STM32F429ZI와 ROS 2를 이용한 2륜 모바일 플랫폼 원격조종 프로젝트

상황실의 버튼 입력을 상황실 STM32가 읽고, 두 노트북 사이의 ROS 2 통신을 거쳐 모바일 플랫폼 STM32로 전달한다. 모바일 STM32는 MDD10A 모터 드라이버를 통해 DC 모터 2개를 제어한다.

현재 전진, 후진, 좌회전, 우회전 및 통신 단절 시 안전정지가 구현되어 있고 그리퍼 서보 제어는 추후 구현할 예정임.

## 1. 시스템 구성

```text
상황실 버튼
  ↓ GPIO
상황실 STM32F429ZI
  ↓ USART3 / USB VCP
상황실 Windows 노트북의 WSL2 Ubuntu
  ↓ ROS 2 / Wi-Fi
모바일 Ubuntu 노트북
  ↓ USART3 / USB VCP
모바일 STM32F429ZI
  ↓ PWM + DIR
MDD10A 모터 드라이버
  ↓
24V DC 기어모터 2개
```

## 2. 주요 하드웨어

- MCU 보드: NUCLEO-F429ZI 2개
- DC 모터: PH42-4266-2481
  - 정격 전압: DC 24V
  - 출력: 47.9W
- 모터 드라이버: Cytron MDD10A
- 구동 방식: 좌우 독립 차동구동

- 통신:
  - STM32와 노트북: USART3 USB Virtual COM Port
  - 노트북 간: ROS 2 DDS 통신
- ROS 2 배포판: Jazzy
- DDS 구현체: CycloneDDS
- ROS Domain ID: 17


## 3. 저장소 구조

```text
ICT/
├── dc_motor/
│   └── 모바일 플랫폼 STM32 프로젝트
├── dc_motor_command/
│   └── 상황실 STM32 프로젝트
└── ros2_ws/
    ├── src/
    │   └── motor_comm/
    │       ├── motor_comm/
    │       │   ├── packet_protocol.py
    │       │   ├── station_serial.py
    │       │   ├── station_node.py
    │       │   ├── mobile_serial.py
    │       │   └── mobile_node.py
    │       ├── package.xml
    │       ├── setup.py
    │       └── setup.cfg
    └── deploy/
        ├── station/
        │   ├── run_station.sh
        │   └── cyclonedds_station.xml
        └── mobile/
            ├── run_mobile.sh
            └── cyclonedds_mobile.xml
```

## 4. 버튼 할당

버튼은 내부 Pull-up 입력으로 구성되며, 버튼을 누르면 LOW 입력

| 비트 | 값 | 상황실 GPIO | 기능 | 현재 상태 |
|---:|---:|---|---|---|
| 0 | `0x01` | PE2 | 전진 | 사용 |
| 1 | `0x02` | PE3 | 후진 | 사용 |
| 2 | `0x04` | PE4 | 좌회전 | 사용 |
| 3 | `0x08` | PE5 | 우회전 | 사용 |
| 4 | `0x10` | PE6 | 그리퍼 1 열기 | 추후 구현 |
| 5 | `0x20` | PE7 | 그리퍼 1 닫기 | 추후 구현 |
| 6 | `0x40` | PE8 | 그리퍼 2 열기 | 추후 구현 |
| 7 | `0x80` | PE9 | 그리퍼 2 닫기 | 추후 구현 |

이동 버튼을 여러 개 동시에 누르거나 아무 버튼도 누르지 않으면 모터가 정지함

## 5. STM32 UART 패킷

두 STM32 프로젝트와 ROS 2 패키지는 동일한 5바이트 패킷을 사용함

| 바이트 | 내용 |
|---:|---|
| 0 | 시작 바이트 `0xAA` |
| 1 | Sequence 번호 |
| 2 | 버튼 상태 |
| 3 | CRC-8 |
| 4 | 종료 바이트 `0x55` |

CRC-8은 Sequence와 버튼 상태를 대상으로 계산하며 Polynomial은 `0x07`임

UART 설정:

- USART3
- TX: PD8
- RX: PD9
- Baud rate: 115200
- Data bits: 8
- Parity: None
- Stop bits: 1

상황실 STM32는 버튼 상태를 50ms마다 전송

## 6. 모바일 STM32 모터 설정

| 기능 | STM32 핀 | 타이머 |
|---|---|---|
| 왼쪽 모터 PWM | PC8 | TIM3 CH3 |
| 오른쪽 모터 PWM | PC7 | TIM3 CH2 |
| 왼쪽 모터 방향 | PG0 | GPIO |
| 오른쪽 모터 방향 | PG1 | GPIO |

- 모터 PWM 주파수: 20kHz
- 현재 시험 속도: 최대 출력값의 40%
- 전진:
  - 왼쪽 모터 전진
  - 오른쪽 모터 전진
- 좌회전:
  - 왼쪽 모터 후진
  - 오른쪽 모터 전진
- 우회전:
  - 왼쪽 모터 전진
  - 오른쪽 모터 후진

## 7. ROS 2 구성

ROS 토픽:

```text
/mobile_platform/button_state
```

메시지 타입:

```text
std_msgs/msg/UInt8
```

노드 구성:

| 노드 | 실행 위치 | 기능 |
|---|---|---|
| `station_node` | 상황실 WSL | 상황실 STM UART 수신 후 ROS 토픽 발행 |
| `mobile_node` | 모바일 Ubuntu | ROS 토픽 구독 후 모바일 STM UART 송신 |

실행 파일 확인:

```bash
ros2 pkg executables motor_comm
```

정상 결과:

```text
motor_comm mobile_node
motor_comm station_node
```

## 8. 상황실 WSL 설정

### 8.1 WSL 네트워크

Windows의 `%USERPROFILE%\.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
```

설정을 변경한 경우 PowerShell에서 실행

```powershell
wsl --shutdown
wsl -d Ubuntu-24.04
```

확인:

```bash
wslinfo --networking-mode
hostname -I
```

현재 상황실 WSL 주소 `192.168.0.121`

### 8.2 STM32를 WSL에 연결

Windows PowerShell에서 장치 확인:

```powershell
usbipd list
```

최초 한 번 관리자 PowerShell에서 공유:

```powershell
usbipd bind --busid <BUSID>
```

WSL에 연결:

```powershell
usbipd attach --wsl --busid <BUSID>
```

WSL에서 확인:

```bash
ls -l /dev/ttyACM*
ls -l /dev/serial/by-id/
```

상황실 STM의 현재 장치 경로:

```text
/dev/serial/by-id/usb-STMicroelectronics_STM32_STLink_066EFF495177514867222628-if02
```

USB BUSID는 USB 포트나 연결 상태에 따라 달라질 수 있으므로 `usbipd list`로 다시 확인함.

### 8.3 상황실 ROS 패키지 빌드

```bash
mkdir -p ~/motor_comm_jazzy_ws/src/motor_comm

cp -a \
/mnt/c/Users/lthst/Desktop/ICT/ros2_ws/src/motor_comm/. \
~/motor_comm_jazzy_ws/src/motor_comm/

cd ~/motor_comm_jazzy_ws

source /opt/ros/jazzy/setup.bash

colcon build \
    --symlink-install \
    --packages-select motor_comm

source install/setup.bash
```

### 8.4 상황실 배포 설정 설치

```bash
mkdir -p ~/.config/motor_comm

install -m 755 \
/mnt/c/Users/lthst/Desktop/ICT/ros2_ws/deploy/station/run_station.sh \
~/run_station.sh

install -m 644 \
/mnt/c/Users/lthst/Desktop/ICT/ros2_ws/deploy/station/cyclonedds_station.xml \
~/.config/motor_comm/cyclonedds_station.xml
```

## 9. 모바일 Ubuntu 노트북 설정

현재 모바일 노트북 주소는 `192.168.0.194`, 네트워크 인터페이스는 `wlo1`이다.

STM 장치 경로:

```text
/dev/serial/by-id/usb-STMicroelectronics_STM32_STLink_0668FF485753667187215421-if02
```

장치 확인:

```bash
ls -l /dev/ttyACM*
ls -l /dev/serial/by-id/
```

필요한 경우 사용자를 `dialout` 그룹에 추가

```bash
sudo usermod -aG dialout "$USER"
```

그룹 변경 후 로그아웃했다가 다시 로그인해야 함.

### 9.1 ROS 패키지 빌드

```bash
cd ~/ICT/ros2_ws

source /opt/ros/jazzy/setup.bash

colcon build \
    --symlink-install \
    --packages-select motor_comm

source install/setup.bash
```

### 9.2 모바일 배포 설정 설치

```bash
mkdir -p ~/.config/motor_comm

install -m 755 \
~/ICT/ros2_ws/deploy/mobile/run_mobile.sh \
~/run_mobile.sh

install -m 644 \
~/ICT/ros2_ws/deploy/mobile/cyclonedds_mobile.xml \
~/.config/motor_comm/cyclonedds_mobile.xml
```

## 10. 실행 방법

안전을 위해 처음 시험할 때는 모바일 플랫폼의 바퀴를 바닥에서 띄운다.

### 10.1 모바일 Ubuntu 노트북

먼저 모바일 노드 실행

```bash
~/run_mobile.sh
```

정상 로그:

```text
Mobile UART opened: ...
Subscribing to: /mobile_platform/button_state
UART buttons: 0x00
```

### 10.2 상황실 WSL

다른 터미널에서 상황실 노드 실행

```bash
~/run_station.sh
```

정상 로그:

```text
Situation UART opened: ...
Publishing to: /mobile_platform/button_state
Sequence: ... | Buttons: 0x00
```

버튼을 누르면 모바일 노드에 같은 버튼 값이 표시되고 모터가 동작함.

종료할 때는 각 터미널에서 `Ctrl+C`

## 11. 안전정지

1. 모바일 ROS 노드 watchdog
   - ROS 명령이 0.5초 동안 수신되지 않으면 `0x00` 정지 명령을 UART로 전송함.

2. 모바일 STM32 watchdog
   - 유효한 UART 패킷이 200ms 동안 수신되지 않으면 모터를 정지함.

ROS 통신이 끊겼을 때 모바일 로그:

```text
ROS command timeout: sending stop
UART buttons: 0x00
```

## 12. 네트워크 주소가 변경된 경우

Wi-Fi가 바뀌면 두 노트북의 IP를 확인한다.

```bash
hostname -I
ip route show default
```

다음 파일의 상대 노트북 주소를 수정해야 함.

상황실 설정:

```text
ros2_ws/deploy/station/cyclonedds_station.xml
```

```xml
<Peer Address="모바일_노트북_IP"/>
```

모바일 설정:

```text
ros2_ws/deploy/mobile/cyclonedds_mobile.xml
```

```xml
<Peer Address="상황실_WSL_IP"/>
```

수정 후 각 노트북의 `~/.config/motor_comm/` 위치에 다시 설치함.

## 13. 문제 해결

### STM 장치가 보이지 않는 경우

```bash
ls -l /dev/ttyACM*
ls -l /dev/serial/by-id/
```

상황실 WSL에서는 Windows PowerShell의 `usbipd list`와 연결 상태도 확인함.

### Serial port 사용 중 오류

다른 터미널, STM32CubeIDE Serial Terminal 또는 Python 프로그램이 동일한 장치를 사용 중인지 확인함.

```bash
sudo lsof /dev/ttyACM0
```

하나의 시리얼 포트는 한 프로그램만 열어야 함.

### ROS 토픽이 다른 노트북에서 보이지 않는 경우

```bash
echo "$ROS_DISTRO"
echo "$ROS_DOMAIN_ID"
echo "$RMW_IMPLEMENTATION"
echo "$CYCLONEDDS_URI"
hostname -I
```

현재 기준값:

```text
ROS_DISTRO=jazzy
ROS_DOMAIN_ID=17
RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

양쪽 노트북의 Ping과 UDP 통신도 확인

### 모터 방향이 반대인 경우

현재 펌웨어는 좌우 모터의 실제 장착 방향을 반영해 서로 다른 전진 DIR 레벨을 사용

```c
LEFT_FORWARD_LEVEL  = GPIO_PIN_RESET
RIGHT_FORWARD_LEVEL = GPIO_PIN_SET
```

배선이나 모터 장착 방향을 변경했다면 이 설정을 다시 확인

## 14. 현재 구현 상태

- [x] 상황실 버튼 입력
- [x] 버튼 디바운싱
- [x] UART 패킷 및 CRC-8
- [x] ROS 2 상황실 노드
- [x] ROS 2 모바일 노드
- [x] 전진·후진·좌회전·우회전
- [x] ROS 통신 단절 안전정지
- [x] STM32 UART 단절 안전정지
- [x] CycloneDDS 고정 피어 통신
- [x] 실행 스크립트 및 배포 설정
- [ ] 그리퍼 서보 하드웨어 선정
- [ ] 그리퍼 1 제어
- [ ] 그리퍼 2 제어
- [ ] 부팅 시 자동 실행
- [ ] 물리 비상정지 장치