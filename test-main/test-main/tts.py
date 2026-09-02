import asyncio
import edge_tts
import pygame
import io

async def speak_edge(text, voice="ko-KR-SunHiNeural", rate="+0%", pitch="+0Hz"):
    # 1. Edge TTS 통신 객체 생성 (텍스트, 목소리, 속도, 음정 설정)
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    
    # 2. 음성 데이터를 메모리에 모으기
    audio_data = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
            
    # 3. 하드디스크 저장 없이 메모리 공간(BytesIO)에 담기
    fp = io.BytesIO(audio_data)
    
    # 4. pygame으로 바로 재생
    pygame.mixer.init()
    pygame.mixer.music.load(fp)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

# 실행 예시
if __name__ == "__main__":
    # 속도 20% 빠르게, 음정 10Hz 높게 설정
    asyncio.run(speak_edge("검은색 옷을 입으신 분들 지뢰 위험 구역입니다, 빠르게 주변을 벗어나 주세요", rate="+20%", pitch="+10Hz"))