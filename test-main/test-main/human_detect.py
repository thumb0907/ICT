import argparse
import os
import time
from pathlib import Path

from camera_stream import CameraStreamServer


def bounded_int(minimum, maximum):
    def convert(value):
        try:
            number = int(value)
        except ValueError as error:
            raise argparse.ArgumentTypeError("정수를 입력하세요.") from error
        if not minimum <= number <= maximum:
            raise argparse.ArgumentTypeError(
                f"{minimum}~{maximum} 범위로 입력하세요."
            )
        return number
    return convert


parser = argparse.ArgumentParser(
    description="RealSense YOLO detection with optional read-only LAN video."
)
parser.add_argument("--stream", action="store_true", help="웹 영상 송출 활성화")
parser.add_argument("--stream-host", default="127.0.0.1",
                    help="외부 노트북 시청 시 0.0.0.0 지정 (신뢰하는 LAN 전용)")
parser.add_argument("--stream-port", type=bounded_int(1, 65535), default=8080)
parser.add_argument("--stream-fps", type=bounded_int(1, 30), default=10)
parser.add_argument("--stream-width", type=bounded_int(160, 1920), default=640)
parser.add_argument("--stream-quality", type=bounded_int(1, 95), default=70)
parser.add_argument("--stream-source", choices=("overlay", "raw"), default="overlay")
parser.add_argument("--headless", action="store_true", help="모바일 로컬 영상 창 생략")
args = parser.parse_args()

# Parse --help before loading the optional camera/ML dependencies.
import cv2
import numpy as np
import pyrealsense2 as rs

from ultralytics import YOLO
from datetime import datetime


# =========================
# 설정값
# =========================
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = str(BASE_DIR / "best.pt")

# VLM이 감시할 폴더
SAVE_DIR = str(BASE_DIR / "content" / "inbox")

WIDTH = 1280
HEIGHT = 720
FPS = 30

CONF = 0.5

MIN_DEPTH = 0.2
MAX_DEPTH = 10.0

# 사진 촬영 최소 간격
# 사람이 계속 감지되어도 5초에 한 번만 촬영
CAPTURE_INTERVAL = 5.0


# =========================
# 폴더 생성
# =========================
os.makedirs(
    SAVE_DIR,
    exist_ok=True
)


# =========================
# YOLO 모델
# =========================
model = YOLO(
    MODEL_PATH
)


# =========================
# 사람 Depth 계산
# =========================
def get_person_depth(
    depth_image,
    x1,
    y1,
    x2,
    y2,
    depth_scale
):

    box_w = x2 - x1
    box_h = y2 - y1

    # Bounding Box 몸통 중앙
    roi_x1 = int(
        x1 + box_w * 0.35
    )

    roi_x2 = int(
        x1 + box_w * 0.65
    )

    roi_y1 = int(
        y1 + box_h * 0.25
    )

    roi_y2 = int(
        y1 + box_h * 0.70
    )


    h, w = depth_image.shape


    roi_x1 = max(
        0,
        min(
            roi_x1,
            w - 1
        )
    )

    roi_x2 = max(
        0,
        min(
            roi_x2,
            w
        )
    )

    roi_y1 = max(
        0,
        min(
            roi_y1,
            h - 1
        )
    )

    roi_y2 = max(
        0,
        min(
            roi_y2,
            h
        )
    )


    if (
        roi_x2 <= roi_x1
        or
        roi_y2 <= roi_y1
    ):
        return None


    # Depth ROI
    roi = depth_image[
        roi_y1:roi_y2,
        roi_x1:roi_x2
    ]


    # 0인 Depth 값 제외
    valid = roi[
        roi > 0
    ]


    if valid.size == 0:
        return None


    # meter 변환
    valid = (
        valid.astype(
            np.float32
        )
        *
        depth_scale
    )


    # 유효 거리 범위
    valid = valid[
        (valid >= MIN_DEPTH)
        &
        (valid <= MAX_DEPTH)
    ]


    if valid.size == 0:
        return None


    # 중앙값 사용
    return float(
        np.median(valid)
    )


# =========================
# 기존 사진 삭제
# =========================
def delete_previous_images():

    # 폴더가 없으면 종료
    if not os.path.exists(
        SAVE_DIR
    ):
        return


    # inbox 내부 파일 확인
    for filename in os.listdir(
        SAVE_DIR
    ):

        # jpg / jpeg 사진만 삭제
        if filename.lower().endswith(
            (".jpg", ".jpeg")
        ):

            file_path = os.path.join(
                SAVE_DIR,
                filename
            )


            try:

                os.remove(
                    file_path
                )

                print(
                    f"[이전 사진 삭제] "
                    f"{file_path}"
                )


            except Exception as e:

                print(
                    f"[사진 삭제 오류] "
                    f"{file_path}"
                )

                print(
                    e
                )


# =========================
# 이미지 저장
# =========================
def save_detection_image(
    color_image,
    total_person
):

    # =========================
    # 새로운 사진을 찍기 전에
    # inbox의 이전 사진 삭제
    # =========================
    delete_previous_images()


    # 현재 시간
    now = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )[:-3]


    # 파일 이름
    filename = (
        f"person_{now}_"
        f"count_{total_person}.jpg"
    )


    # 최종 저장 경로
    final_path = os.path.join(
        SAVE_DIR,
        filename
    )


    # =========================
    # 저장 중 VLM이 읽지 못하도록
    # 임시 파일에 먼저 저장
    # =========================
    temp_path = (
        final_path + ".tmp.jpg"
    )


    success = cv2.imwrite(
        temp_path,
        color_image
    )


    if not success:

        print(
            "[오류] 이미지 저장 실패"
        )

        return None


    # =========================
    # 이미지 저장이 완전히 끝난 후
    # 정상 jpg 파일명으로 변경
    # =========================
    os.replace(
        temp_path,
        final_path
    )


    print()

    print(
        "=============================="
    )

    print(
        f"[사진 저장] "
        f"사람 {total_person}명"
    )

    print(
        final_path
    )

    print(
        "=============================="
    )

    print()


    return final_path


# =========================
# RealSense 설정
# =========================
pipeline = rs.pipeline()

config = rs.config()


# Depth Stream
config.enable_stream(
    rs.stream.depth,
    WIDTH,
    HEIGHT,
    rs.format.z16,
    FPS
)


# Color Stream
config.enable_stream(
    rs.stream.color,
    WIDTH,
    HEIGHT,
    rs.format.bgr8,
    FPS
)


# =========================
# 마지막 사진 촬영 시간
# =========================
# 0.0으로 시작하면
# 처음 사람이 감지됐을 때 즉시 촬영 가능
last_capture_time = 0.0
last_stream_time = 0.0
stream_server = None
pipeline_started = False


# =========================
# 메인 루프
# =========================
try:
    profile = pipeline.start(config)
    pipeline_started = True
    depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()
    align = rs.align(rs.stream.color)

    if args.stream:
        stream_server = CameraStreamServer(args.stream_host, args.stream_port)
        stream_server.start()
        print(f"[영상 송출] http://{args.stream_host}:{stream_server.port}/")
        print("[영상 송출] 다른 노트북은 위 주소의 호스트를 모바일의 실제 IP로 바꾸세요.")
        print("[주의] 인증 없는 LAN 전용 영상입니다. 인터넷에 공개하지 마세요.")

    while True:

        # =========================
        # RealSense 프레임
        # =========================
        frames = (
            pipeline
            .wait_for_frames()
        )


        # Depth를 Color 좌표에 정렬
        aligned_frames = (
            align.process(
                frames
            )
        )


        depth_frame = (
            aligned_frames
            .get_depth_frame()
        )


        color_frame = (
            aligned_frames
            .get_color_frame()
        )


        # 정상 프레임이 없으면 다음 프레임
        if (
            not depth_frame
            or
            not color_frame
        ):
            continue


        # =========================
        # RGB 영상
        # =========================
        color_image = np.asanyarray(
            color_frame.get_data()
        )


        # =========================
        # Depth 영상
        # =========================
        depth_image = np.asanyarray(
            depth_frame.get_data()
        )


        # =========================
        # YOLO 사람 탐지
        # =========================
        results = model(
            color_image,
            classes=[0],
            conf=CONF,
            verbose=False
        )


        result = results[0]


        boxes = (
            result.boxes
        )


        # YOLO Bounding Box
        display_image = (
            result.plot()
        )


        # =========================
        # 총 사람 수
        # =========================
        if boxes is not None:

            total_person = len(
                boxes
            )

        else:

            total_person = 0


        # =========================
        # 각 사람 거리 표시
        # =========================
        if (
            boxes is not None
            and
            len(boxes) > 0
        ):

            for box in boxes.xyxy:

                x1, y1, x2, y2 = map(
                    int,
                    box.tolist()
                )


                # Depth 계산
                distance = (
                    get_person_depth(
                        depth_image,
                        x1,
                        y1,
                        x2,
                        y2,
                        depth_scale
                    )
                )


                # 거리 표시 문자열
                if distance is not None:

                    text = (
                        f"{distance:.2f} m"
                    )

                else:

                    text = (
                        "Depth N/A"
                    )


                # =========================
                # 검은색 외곽선
                # =========================
                cv2.putText(
                    display_image,
                    text,
                    (
                        x1 + 5,
                        y1 + 30
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 0),
                    4,
                    cv2.LINE_AA
                )


                # =========================
                # 흰색 글자
                # =========================
                cv2.putText(
                    display_image,
                    text,
                    (
                        x1 + 5,
                        y1 + 30
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA
                )


        # =========================
        # Total Person 표시
        # =========================
        total_text = (
            f"Total Person: {total_person}"
        )


        # 검은색 외곽선
        cv2.putText(
            display_image,
            total_text,
            (20, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 0),
            5,
            cv2.LINE_AA
        )


        # 흰색 글자
        cv2.putText(
            display_image,
            total_text,
            (20, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )


        # =========================
        # 사람 감지 시
        # 최대 5초에 한 번 촬영
        # =========================
        current_time = time.monotonic()

        # 카메라를 다시 열지 않고 최신 프레임을 한 번만 인코딩해 공유합니다.
        # HTTP 쓰기는 별도 스레드에서 실행되어 느린 시청자를 기다리지 않습니다.
        if (
            stream_server is not None
            and current_time - last_stream_time >= 1.0 / args.stream_fps
        ):
            stream_image = (
                display_image if args.stream_source == "overlay" else color_image
            )
            source_height, source_width = stream_image.shape[:2]
            if source_width > args.stream_width:
                stream_image = cv2.resize(
                    stream_image,
                    (args.stream_width,
                     max(1, round(source_height * args.stream_width / source_width))),
                    interpolation=cv2.INTER_AREA,
                )
            encoded, jpeg = cv2.imencode(
                ".jpg", stream_image,
                [cv2.IMWRITE_JPEG_QUALITY, args.stream_quality],
            )
            if encoded:
                stream_server.publish(jpeg.tobytes())
            last_stream_time = current_time


        if (
            total_person >= 1
            and
            current_time - last_capture_time
            >= CAPTURE_INTERVAL
        ):

            saved_path = (
                save_detection_image(
                    color_image,
                    total_person
                )
            )


            # 이미지 저장 성공 시에만
            # 마지막 촬영 시간 갱신
            if saved_path is not None:

                last_capture_time = (
                    current_time
                )


        # =========================
        # 영상 출력
        # =========================
        if not args.headless:
            cv2.imshow("YOLO Human Detection + Depth", display_image)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                break


# =========================
# 종료
# =========================
except KeyboardInterrupt:
    print("\n카메라 종료")

finally:
    if stream_server is not None:
        stream_server.stop()

    if pipeline_started:
        pipeline.stop()

    if not args.headless:
        cv2.destroyAllWindows()
