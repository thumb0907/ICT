import os
import re
import time
import shutil
import asyncio
import io

import edge_tts
import pygame

from PIL import Image
from google import genai


# =========================
# 설정
# =========================
WATCH_DIR = "./content/inbox"
PROCESSED_DIR = "./content/processed"

GEMINI_MODEL = "gemini-3.1-flash-lite"


# =========================
# Edge TTS 설정
# =========================
TTS_VOICE = "ko-KR-SunHiNeural"

# 음성 속도
TTS_RATE = "+20%"

# 음정
TTS_PITCH = "+10Hz"


# =========================
# Gemini API
# =========================
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

client = genai.Client(api_key=api_key)


# =========================
# 폴더 생성
# =========================
os.makedirs(
    WATCH_DIR,
    exist_ok=True
)

os.makedirs(
    PROCESSED_DIR,
    exist_ok=True
)


# =========================
# pygame 오디오 초기화
# =========================
pygame.mixer.init()


# =========================
# Prompt
# =========================
def build_prompt(
    total_person
):

    # =========================
    # 1명 / 2명 이상에 따라
    # 출력 표현을 다르게 지정
    # =========================
    if total_person == 1:

        person_phrase = "분께"

        output_example = (
            "검은색 상의를 입으신 분께 경고합니다. "
            "현재 지뢰 위험 지역에 진입하셨습니다. "
            "즉시 안전 구역으로 이동해 주세요."
        )

    else:

        person_phrase = "분들께"

        output_example = (
            "검은색 상의, 회색 상의를 입으신 분들께 경고합니다. "
            "현재 지뢰 위험 지역에 진입하셨습니다. "
            "즉시 안전 구역으로 이동해 주세요."
        )


    return f"""
당신은 위험 지역 감시 카메라의 시각 분석 시스템입니다.

현재 YOLO 객체 탐지 모델이 이 이미지에서 총 {total_person}명의 사람을 감지했습니다.

YOLO가 감지한 사람 수는 정확히 {total_person}명입니다.

이미지에 보이는 사람들을 왼쪽에서 오른쪽 순서로 확인하세요.

각 사람마다 가장 명확하게 확인할 수 있는 옷 특징을 정확히 하나씩 추출하세요.


의류 표현 규칙:

의류 종류는 반드시 다음 두 단어 중 하나만 사용하세요.

- 상의
- 하의

구체적인 의류 이름은 절대 사용하지 마세요.

예를 들어:

티셔츠 → 상의
반팔 → 상의
긴팔 → 상의
셔츠 → 상의
후드티 → 상의
재킷 → 상의
점퍼 → 상의
코트 → 상의
조끼 → 상의

바지 → 하의
청바지 → 하의
반바지 → 하의
치마 → 하의


각 사람의 특징은 반드시 다음 형식으로 표현하세요.

"[색상] 상의"

또는

"[색상] 하의"


출력 규칙:

1. 현재 감지 인원은 정확히 {total_person}명입니다.

2. 사람이 1명이면 반드시
"분께 경고합니다."
라는 단수 표현을 사용하세요.

3. 사람이 2명 이상이면 반드시
"분들께 경고합니다."
라는 복수 표현을 사용하세요.

4. 현재 이번 응답에서는 반드시
"{person_phrase} 경고합니다."
라고 출력하세요.

5. "사람 1", "사람 2", "첫 번째 사람", "두 번째 사람" 등의 번호 표현은 절대 사용하지 마세요.

6. 이미지에 보이는 사람들을 왼쪽에서 오른쪽 순서대로 분석하세요.

7. 사람마다 옷 특징은 정확히 하나만 출력하세요.

8. 각 특징은 반드시
"색상 + 상의"
또는
"색상 + 하의"
형식으로 출력하세요.

9. 티셔츠, 후드티, 재킷, 셔츠, 바지, 청바지 등의 구체적인 옷 이름은 절대 출력하지 마세요.

10. 사람마다 추출한 특징은 쉼표로 구분하세요.

11. 성별, 나이, 인종, 신원 등은 추측하지 마세요.

12. 이미지에서 명확하게 확인되는 정보만 사용하세요.

13. 불필요한 설명이나 분석 과정은 절대 출력하지 마세요.

14. 반드시 자연스러운 한국어 한 문장으로 출력하세요.

15. 옷 특징 뒤에는 반드시 다음 경고 문장을 이어서 출력하세요.

현재 지뢰 위험 지역에 진입하셨습니다. 즉시 안전 구역으로 이동해 주세요.


현재 {total_person}명에 대한 올바른 출력 예시는 다음과 같습니다.

{output_example}


다른 설명, 분석 과정, 인사말은 절대 출력하지 마세요.
""".strip()


# =========================
# 파일명에서 사람 수 추출
# =========================
def get_person_count(
    image_path
):

    filename = os.path.basename(
        image_path
    )


    match = re.search(
        r"_count_(\d+)\.jpg$",
        filename
    )


    if match:

        return int(
            match.group(1)
        )


    return 1


# =========================
# Gemini 결과 후처리
# =========================
def normalize_result(
    result,
    total_person
):

    # =========================
    # 줄바꿈 / 불필요한 공백 제거
    # =========================
    result = " ".join(
        result.split()
    )


    # =========================
    # 구체적인 의류 이름을
    # 상의 / 하의로 강제 통일
    # =========================
    upper_words = [
        "티셔츠",
        "반팔",
        "긴팔",
        "셔츠",
        "후드티",
        "후드",
        "재킷",
        "자켓",
        "점퍼",
        "코트",
        "조끼"
    ]

    lower_words = [
        "청바지",
        "반바지",
        "긴바지",
        "바지",
        "치마"
    ]


    for word in upper_words:

        result = result.replace(
            word,
            "상의"
        )


    for word in lower_words:

        result = result.replace(
            word,
            "하의"
        )


    # =========================
    # 1명 / 여러 명 표현 강제 보정
    # =========================
    if total_person == 1:

        result = result.replace(
            "분들께",
            "분께"
        )

        result = result.replace(
            "분들을",
            "분을"
        )

        result = result.replace(
            "분들이",
            "분이"
        )


    else:

        # 이미 분들께라면 그대로 두고
        # 단수형만 복수형으로 변경
        if "분들께" not in result:

            result = result.replace(
                "분께",
                "분들께"
            )


    return result


# =========================
# Gemini VLM
# =========================
def analyze_image(
    image_path,
    total_person
):

    prompt = build_prompt(
        total_person
    )


    image = Image.open(
        image_path
    )


    try:

        response = (
            client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[
                    prompt,
                    image
                ]
            )
        )


    finally:

        image.close()


    result = (
        response
        .text
        .strip()
    )


    # =========================
    # Gemini 출력 최종 보정
    # =========================
    result = normalize_result(
        result,
        total_person
    )


    return result


# =========================
# Edge TTS
# =========================
async def speak_edge(
    text,
    voice=TTS_VOICE,
    rate=TTS_RATE,
    pitch=TTS_PITCH
):

    print(
        "[TTS 변환 시작]"
    )


    # =========================
    # Edge TTS 통신 객체 생성
    # =========================
    communicate = edge_tts.Communicate(
        text,
        voice,
        rate=rate,
        pitch=pitch
    )


    # =========================
    # 음성 데이터를 메모리에 저장
    # =========================
    audio_data = bytearray()


    async for chunk in communicate.stream():

        if chunk["type"] == "audio":

            audio_data.extend(
                chunk["data"]
            )


    # =========================
    # 음성 데이터 확인
    # =========================
    if len(audio_data) == 0:

        raise RuntimeError(
            "Edge TTS에서 음성 데이터를 받지 못했습니다."
        )


    # =========================
    # 메모리 파일 생성
    # =========================
    fp = io.BytesIO(
        audio_data
    )

    fp.seek(0)


    # =========================
    # pygame으로 바로 재생
    # =========================
    pygame.mixer.music.load(
        fp
    )


    pygame.mixer.music.play()


    print(
        "[TTS 음성 출력 시작]"
    )


    # =========================
    # 음성이 끝날 때까지 대기
    # =========================
    while pygame.mixer.music.get_busy():

        await asyncio.sleep(
            0.05
        )


    print(
        "[TTS 음성 출력 완료]"
    )


# =========================
# 동기 코드에서 Edge TTS 실행
# =========================
def speak_text(
    text
):

    asyncio.run(
        speak_edge(
            text,
            voice=TTS_VOICE,
            rate=TTS_RATE,
            pitch=TTS_PITCH
        )
    )


# =========================
# 처리 완료 이미지 이동
# =========================
def move_to_processed(
    image_path
):

    filename = os.path.basename(
        image_path
    )


    destination = os.path.join(
        PROCESSED_DIR,
        filename
    )


    # =========================
    # 동일한 이름의 파일이 있으면 삭제
    # =========================
    if os.path.exists(
        destination
    ):

        os.remove(
            destination
        )


    shutil.move(
        image_path,
        destination
    )


# =========================
# 메인 VLM Worker
# =========================
print(
    "================================"
)

print(
    "Gemini VLM Worker 시작"
)

print(
    f"감시 폴더: {WATCH_DIR}"
)

print(
    "새 이미지 대기 중..."
)

print(
    f"TTS Voice: {TTS_VOICE}"
)

print(
    f"TTS Rate: {TTS_RATE}"
)

print(
    f"TTS Pitch: {TTS_PITCH}"
)

print(
    "================================"
)


try:

    while True:

        # =========================
        # inbox에 있는 jpg 검색
        # =========================
        images = [

            f

            for f in os.listdir(
                WATCH_DIR
            )

            if f.lower().endswith(
                ".jpg"
            )
        ]


        # =========================
        # 오래된 사진부터 처리
        # =========================
        images.sort()


        # =========================
        # 사진 없으면 대기
        # =========================
        if len(images) == 0:

            time.sleep(
                0.2
            )

            continue


        # =========================
        # 첫 번째 이미지
        # =========================
        filename = images[0]


        image_path = os.path.join(
            WATCH_DIR,
            filename
        )


        # =========================
        # YOLO 감지 인원
        # =========================
        total_person = (
            get_person_count(
                image_path
            )
        )


        print()

        print(
            "=============================="
        )

        print(
            "[새 이미지]"
        )

        print(
            image_path
        )

        print(
            f"YOLO 감지 인원: "
            f"{total_person}명"
        )


        try:

            # =========================
            # 1. Gemini VLM 분석
            # =========================
            alert_text = (
                analyze_image(
                    image_path,
                    total_person
                )
            )


            print(
                "[Gemini 결과]"
            )

            print(
                alert_text
            )


            # =========================
            # 2. Edge TTS 음성 출력
            # =========================
            print(
                "[Edge TTS]"
            )


            speak_text(
                alert_text
            )


            # =========================
            # 3. 완료 이미지 이동
            # =========================
            move_to_processed(
                image_path
            )


            print(
                "[처리 완료]"
            )

            print(
                "=============================="
            )


        except Exception as e:

            print(
                "[Gemini/TTS 처리 오류]"
            )

            print(
                e
            )


            # =========================
            # 오류 발생 시
            # 이미지를 삭제하지 않고
            # inbox에 그대로 유지
            # =========================
            print(
                "5초 후 다시 시도합니다."
            )


            time.sleep(
                5
            )


# =========================
# Ctrl + C 종료
# =========================
except KeyboardInterrupt:

    print()

    print(
        "VLM Worker 종료"
    )


# =========================
# 프로그램 종료
# =========================
finally:

    pygame.mixer.music.stop()

    pygame.mixer.quit()
