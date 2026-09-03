"""Read-only, latest-frame MJPEG server for a trusted local network.

This module never opens a camera and has no third-party dependencies.
The capture process publishes one encoded JPEG shared by all viewers.
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


VIEWER_HTML = """<!doctype html>
<html lang="ko">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>모바일 플랫폼 카메라</title>
<style>
body { margin: 0; background: #111827; color: #e5e7eb;
       font: 16px system-ui, sans-serif; }
main { max-width: 1100px; margin: auto; padding: 20px; }
h1 { font-size: 24px; }
#status { color: #fbbf24; }
img { display: block; width: 100%; background: #000; min-height: 160px; }
button { padding: 10px 18px; cursor: pointer; }
.note { color: #cbd5e1; line-height: 1.6; }
</style>
<main>
<h1>모바일 플랫폼 · 카메라</h1>
<p id="status" role="status" aria-live="polite">카메라 상태 확인 중…</p>
<img id="video" alt="모바일 카메라 영상">
<p><button id="reconnect">영상 다시 연결</button></p>
<p class="note">영상 전용 · 조종 명령과 음성은 전송하지 않습니다.<br>
표시 상태는 서버의 프레임 생성 상태입니다. 수신 영상의 실제 지연을 보장하지 않습니다.
화면이 멈추거나 통신이 끊기면 주행을 멈추세요.</p>
</main>
<script>
const video = document.getElementById('video');
const statusText = document.getElementById('status');
let streamOpen = false;
function closeStream() {
  video.removeAttribute('src');
  video.style.visibility = 'hidden';
  streamOpen = false;
}
function openStream() {
  video.src = '/stream.mjpg?t=' + Date.now();
  video.style.visibility = 'visible';
  streamOpen = true;
}
video.onerror = () => { closeStream(); };
document.getElementById('reconnect').onclick = () => { closeStream(); };
async function checkStatus() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 2000);
  try {
    const response = await fetch('/health', {
      cache: 'no-store', signal: controller.signal
    });
    const state = await response.json();
    if (!state.ready) {
      statusText.textContent = '영상 대기 / 중단 — 카메라 프로그램을 확인하세요.';
      statusText.style.color = '#fbbf24';
      closeStream();
    } else {
      statusText.textContent = '송출 중 · 서버 프레임 #' + state.sequence
        + ' · ' + state.age_seconds.toFixed(1) + '초 전 생성';
      statusText.style.color = '#86efac';
      if (!streamOpen) openStream();
    }
  } catch (error) {
    statusText.textContent = '연결 끊김 — 오래된 영상을 숨겼습니다.';
    statusText.style.color = '#fbbf24';
    closeStream();
  } finally {
    clearTimeout(timer);
    setTimeout(checkStatus, 1000);
  }
}
checkStatus();
</script>
</html>
""".encode("utf-8")


class LatestFrame:
    """A one-frame buffer: slow viewers never build a capture-side queue."""

    def __init__(self, stale_after=3.0):
        self.condition = threading.Condition()
        self.jpeg = None
        self.sequence = 0
        self.updated_at = None
        self.closed = False
        self.stale_after = stale_after

    def publish(self, jpeg):
        with self.condition:
            if not self.closed:
                self.jpeg = bytes(jpeg)
                self.sequence += 1
                self.updated_at = time.monotonic()
                self.condition.notify_all()

    def wait_next(self, previous_sequence, timeout=1.0):
        with self.condition:
            self.condition.wait_for(
                lambda: self.closed or self.sequence != previous_sequence,
                timeout=timeout,
            )
            if self.closed or self.sequence == previous_sequence:
                return None
            return self.sequence, self.jpeg

    def snapshot(self):
        with self.condition:
            age = (
                None if self.updated_at is None
                else time.monotonic() - self.updated_at
            )
            ready = (
                not self.closed and self.jpeg is not None
                and age is not None and age <= self.stale_after
            )
            return {
                "ready": ready,
                "sequence": self.sequence,
                "age_seconds": None if age is None else round(age, 3),
            }, self.jpeg

    def close(self):
        with self.condition:
            self.closed = True
            self.condition.notify_all()


class CameraStreamServer:
    """Small LAN viewer, not an authenticated/public internet service."""

    def __init__(self, host="127.0.0.1", port=8080, max_viewers=4,
                 stale_after=3.0):
        self.frames = LatestFrame(stale_after=stale_after)
        self.viewer_slots = threading.BoundedSemaphore(max_viewers)
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                super().setup()
                # A stalled reader cannot hold a writer indefinitely.
                self.connection.settimeout(3.0)

            def log_message(self, format, *args):
                # Avoid one access-log line per viewer health poll.
                pass

            def reply(self, status, content_type, payload):
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(payload)

            def do_GET(self):
                try:
                    path = urlsplit(self.path).path
                    if path == "/":
                        self.reply(200, "text/html; charset=utf-8", VIEWER_HTML)
                    elif path == "/health":
                        state, _ = owner.frames.snapshot()
                        self.reply(
                            200 if state["ready"] else 503,
                            "application/json", json.dumps(state).encode(),
                        )
                    elif path == "/snapshot.jpg":
                        state, jpeg = owner.frames.snapshot()
                        if state["ready"]:
                            self.reply(200, "image/jpeg", jpeg)
                        else:
                            self.reply(503, "text/plain", b"No fresh frame")
                    elif path == "/stream.mjpg":
                        self.stream()
                    else:
                        self.reply(404, "text/plain", b"Not found")
                except (OSError, TimeoutError):
                    # Browser tab closed, client disconnected, or slow reader.
                    pass

            def stream(self):
                state, _ = owner.frames.snapshot()
                if not state["ready"]:
                    self.reply(503, "text/plain", b"No fresh frame")
                    return
                if not owner.viewer_slots.acquire(blocking=False):
                    self.reply(503, "text/plain", b"Viewer limit reached")
                    return
                try:
                    self.send_response(200)
                    self.send_header(
                        "Content-Type",
                        "multipart/x-mixed-replace; boundary=frame",
                    )
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    sequence = 0
                    while not owner.frames.closed:
                        item = owner.frames.wait_next(sequence)
                        if item is None:
                            state, _ = owner.frames.snapshot()
                            if not state["ready"]:
                                break
                            continue
                        sequence, jpeg = item
                        header = (
                            "--frame\r\nContent-Type: image/jpeg\r\n"
                            f"Content-Length: {len(jpeg)}\r\n"
                            f"X-Frame-Sequence: {sequence}\r\n\r\n"
                        ).encode("ascii")
                        self.wfile.write(header + jpeg + b"\r\n")
                        self.wfile.flush()
                finally:
                    owner.viewer_slots.release()

        self.httpd = ThreadingHTTPServer((host, port), Handler)
        self.thread = None

    @property
    def port(self):
        return self.httpd.server_address[1]

    def start(self):
        if self.thread is not None:
            raise RuntimeError("Camera stream server already started")
        self.thread = threading.Thread(
            target=self.httpd.serve_forever, kwargs={"poll_interval": 0.1},
            name="camera-http", daemon=True,
        )
        self.thread.start()

    def publish(self, jpeg):
        self.frames.publish(jpeg)

    def stop(self):
        self.frames.close()
        if self.thread is not None:
            self.httpd.shutdown()
            self.thread.join(timeout=2.0)
        self.httpd.server_close()
