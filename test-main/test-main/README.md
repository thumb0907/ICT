# 모바일 카메라·VLM 실행 및 상황실 영상 시청

모바일 노트북(Humble)은 주행 명령 수신, RealSense/YOLO, Gemini 요청/TTS,
영상 송출을 담당합니다. 상황실 노트북은 `station_node`로 조종하고
브라우저로 영상만 봅니다. 다른 Ubuntu/Windows 노트북도 브라우저만 있으면 됩니다.

## 구성과 주의사항

- `mobile_node`: 기존 ROS → 모바일 STM 통신. 카메라/VLM과 별도 프로세스입니다.
- `human_detect.py`: RealSense를 한 번 열어 YOLO와 거리 계산을 수행합니다.
  `--stream`을 지정하면 같은 프레임을 JPEG로 인코딩해 HTTP로 전달합니다.
- `vlm_worker.py`: `content/inbox` 사진을 Gemini API로 보내 분석하고,
  Edge TTS로 변환한 음성을 모바일 노트북 스피커에서 재생합니다.
  **VLM 추론은 로컬 모델이 아니라 클라우드 API이며 인터넷이 필요합니다.**
- 영상 시청은 ROS/DDS와 무관한 HTTP 통신입니다. API 키는 시청자에게 필요하지 않습니다.
- 영상 서버는 **인증/암호화 없는 신뢰하는 LAN의 시험용 서버**입니다.
  모바일의 송출 포트를 인터넷에 포트 포워딩하지 마세요.
  방화벽을 사용할 경우 필요한 시청 노트북만 허용하세요.
- 별도 프로세스여도 CPU/GPU 및 Wi-Fi 대역폭은 공유합니다.
  처음에는 구동부를 안전하게 정지한 상태에서 영상을 시험하세요.
  통신 단절 정지 기능이 물리 비상정지를 대체하지 않습니다.

## 1. 모바일 코드 갱신

이 변경이 원격 저장소에 커밋/푸시된 뒤 모바일에서 실행합니다.
아직 로컬에만 수정돼 있으면 `git pull`만으로 새 기능을 받을 수 없습니다.

```bash
cd ~/ICT
git status --short
git pull --ff-only
```

로컬 수정이 있다면 먼저 확인하고 보존하세요. 강제로 초기화하지 마세요.
STM 펌웨어나 ROS 패키지는 이 영상 기능 때문에 다시 빌드할 필요가 없습니다.

## 2. 모바일의 카메라/VLM Python 환경

이미 RealSense·YOLO·VLM이 동작하는 환경이 있으면 **그 환경을 그대로 사용**하세요.
`camera_stream.py` 자체는 Python 표준 라이브러리만 사용하므로
Flask 등 추가 설치는 필요하지 않습니다.

환경이 없다면 Ubuntu에서 아래와 같이 별도 환경을 만들 수 있습니다.
카메라의 OS/USB 설정과 GPU용 PyTorch 설정은 별도이며, pip 설치만으로
하드웨어 동작을 보장하지는 않습니다.

```bash
sudo apt update
sudo apt install python3-venv
cd ~/ICT/test-main/test-main
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

ROS 제어 터미널에서는 이 가상환경을 활성화하지 마세요.
카메라와 VLM 두 터미널에서만 활성화합니다.
`best.pt`는 이 디렉터리에 있어야 하며 RealSense는 모바일에 USB로 연결합니다.
RealSense Viewer 등 같은 카메라를 사용하는 다른 프로그램은 종료하세요.

## 3. 모바일 터미널 A: 주행·그리퍼 명령 수신

기존 정상 동작했던 DDS XML과 USB 설정을 사용합니다.
저장소의 기존 `run_mobile.sh`는 Jazzy 경로를 사용하므로 **Humble에서는
아래 명령을 사용**하세요. 영상 추가를 이유로 DDS XML을 덮어쓰지 마세요.

```bash
source /opt/ros/humble/setup.bash
source ~/ICT/ros2_ws/install/setup.bash
export ROS_DOMAIN_ID=17
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_LOCALHOST_ONLY=0
export CYCLONEDDS_URI="file://$HOME/.config/motor_comm/cyclonedds_mobile.xml"
ls -l /dev/serial/by-id/

ros2 run motor_comm mobile_node --ros-args \
  -p port:=/dev/serial/by-id/usb-STMicroelectronics_STM32_STLink_0668FF485753667187215421-if02
```

STM이 교체됐다면 실제 `/dev/serial/by-id/` 이름에 맞게 수정하세요.

## 4. 모바일 터미널 B: 카메라·YOLO·영상 송출

```bash
cd ~/ICT/test-main/test-main
source .venv/bin/activate
python human_detect.py --stream --stream-host 0.0.0.0 --headless
```

`source .venv/bin/activate`는 2단계에서 해당 환경을 만든 경우의 명령입니다.
기존 Python 환경을 사용한다면 그 환경을 활성화하세요.

- 기본 송출: 탐지 박스·거리·인원 수 포함, 가로 640픽셀, JPEG 품질 70, 최대 10fps.
- 원래 YOLO/Depth 입력은 1280×720, 요청 카메라 FPS는 30으로 유지합니다.
- 실제 송출 속도는 YOLO 처리 속도 이하입니다. 10fps는 보장값이 아니라 상한입니다.
- 원본 RGB 송출: `--stream-source raw` 추가.
- 모바일에서도 영상 창 표시: `--headless` 제외.
- `--stream`을 생략하면 웹 서버를 열지 않습니다.
- 호스트 기본값은 `127.0.0.1`입니다. 원격 시청 시 `--stream-host 0.0.0.0`이 필요합니다.
- 시청자는 최대 4개 MJPEG 연결을 사용할 수 있습니다. 탭마다 연결 1개입니다.

핫스팟 대역폭이 부족하면:

```bash
python human_detect.py --stream --stream-host 0.0.0.0 --headless \
  --stream-width 480 --stream-fps 5 --stream-quality 60
```

## 5. 모바일 터미널 C: Gemini·음성 출력

먼저 Google Cloud에서 이전에 노출된 키를 폐기/교체하세요.
새 키를 코드, README, Git 커밋에 넣지 마세요.
아래 입력은 화면과 셸 명령 기록에 키 값을 남기지 않습니다.

```bash
cd ~/ICT/test-main/test-main
source .venv/bin/activate
read -rsp '새 GEMINI_API_KEY 입력: ' GEMINI_API_KEY
echo
export GEMINI_API_KEY
python vlm_worker.py
```

사람이 감지되면 기존처럼 최대 5초에 한 번 사진을 저장하고 VLM이 처리합니다.
VLM을 켜지 않아도 카메라 영상은 볼 수 있습니다.
카메라와 VLM의 데이터 경로는 스크립트 위치를 기준으로 하므로
서로 다른 작업 디렉터리에서 실행해도 같은 `content/inbox`를 사용합니다.

## 6. 상황실: 조종 노드 + 웹 영상

### 조종 노드 (Windows의 WSL Jazzy)

WSL 창을 열어 둔 상태로 PowerShell에서 `usbipd list`를 확인하고,
상황실 ST-Link를 현재 BUSID로 `usbipd attach --wsl --busid <BUSID>` 합니다.
이전 `3-4` 등의 번호는 재연결 시 바뀔 수 있으므로 그대로 가정하지 마세요.

WSL에서 기존 조종 명령을 실행합니다.

```bash
source /opt/ros/jazzy/setup.bash
source ~/motor_comm_jazzy_ws/install/setup.bash
export ROS_DOMAIN_ID=17
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
unset ROS_LOCALHOST_ONLY
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
export CYCLONEDDS_URI="file://$HOME/.config/motor_comm/cyclonedds_station.xml"
ls -l /dev/serial/by-id/

ros2 run motor_comm station_node --ros-args \
  -p port:=/dev/serial/by-id/usb-STMicroelectronics_STM32_STLink_066EFF495177514867222628-if02
```

### 영상 시청 (Windows 또는 Ubuntu 브라우저)

모바일에서 `ip -br -4 address`로 **현재 Wi-Fi IPv4 주소**를 확인합니다.
그 주소가 예를 들어 `10.247.18.155`라면 시청 노트북의 브라우저에 입력합니다.

```text
http://10.247.18.155:8080/
```

`0.0.0.0`이나 시청 노트북의 `localhost`가 아니라 **모바일의 IP**입니다.
다른 Ubuntu 노트북도 같은 주소로 접속하면 되고, 영상만 보기 위해
ROS, YOLO, API 키, RealSense 드라이버를 설치할 필요는 없습니다.
오디오는 전송하지 않습니다.

서버가 새 프레임을 3초 넘게 만들지 못하거나 상태 요청에 실패하면
웹 화면은 경고와 함께 오래된 영상을 숨깁니다. 이 상태는 **서버 측 프레임
신선도**이며 수신 영상의 실제 지연 측정이나 주행 안전 보장이 아닙니다.

## 7. 연결 확인 / 문제 해결

모바일 자신에서 먼저 확인합니다.

```bash
curl -i http://127.0.0.1:8080/health
ss -ltn 'sport = :8080'
```

정상: HTTP 200, `"ready": true`. 카메라 대기/3초 이상 정지: HTTP 503.
카메라 프로그램이 종료됐으면 연결 거부/타임아웃이 나올 수 있습니다.

원격 Ubuntu에서 (IP는 현재 모바일 주소로 교체):

```bash
curl --max-time 5 -i http://10.247.18.155:8080/health
```

- 모바일에서만 된다면 같은 Wi-Fi/핫스팟인지, 모바일 IP,
  `--stream-host 0.0.0.0`, 모바일의 TCP 8080 방화벽을 확인합니다.
  핫스팟의 기기 간 격리가 켜져 있으면 같은 SSID라도 통신이 안 될 수 있습니다.
- UFW가 **설치되어 활성화된 경우에만**, 필요한 시청자 주소로 제한해 허용합니다.
  예: `sudo ufw allow from 10.247.18.23 to any port 8080 proto tcp`.
  실제 시청 Windows IP가 WSL IP와 다르면 Windows의 현재 주소를 사용하세요.
  UFW 설치/전체 방화벽 해제는 필요하지 않습니다.
- `Address already in use`: 다른 카메라 송출 프로세스를 종료하거나
  `--stream-port 8081`을 지정하고 브라우저 주소도 바꿉니다.
- `No device connected`: RealSense의 USB/권한 및 다른 프로그램 점유 여부를 확인합니다.
- `GEMINI_API_KEY` 오류: VLM을 실행하는 **같은 터미널**에서 새 키를 export합니다.
- 인식은 되는데 영상이 느리면 송출 해상도/FPS/품질을 낮추고 모바일의 GPU 사용을 확인합니다.
- 핫스팟 IP가 바뀌면 영상 URL뿐 아니라 기존 조종용 DDS XML의 피어 주소도 확인합니다.

종료는 각 터미널의 `Ctrl+C`입니다. 먼저 플랫폼을 정지시키고 조종/주행 노드를 종료하세요.

## 하드웨어 없이 하는 테스트

```bash
cd test-main/test-main
python -m unittest discover -s tests -v
```

이 테스트는 최신 프레임 공유, MJPEG 형식, 여러 시청자, 끊김/정지 상태,
읽기 전용 경로와 CLI 검증만 확인합니다. RealSense, GPU, Gemini, STM,
실제 핫스팟 성능은 대상 노트북에서 별도 확인해야 합니다.
