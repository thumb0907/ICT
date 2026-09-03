"""Camera/GPU/ROS-free regression tests for the read-only video server."""

import http.client
import json
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from camera_stream import CameraStreamServer, LatestFrame


class LatestFrameTests(unittest.TestCase):
    def test_latest_only_and_immutable_copy(self):
        frames = LatestFrame()
        frames.publish(b"first")
        payload = bytearray(b"latest")
        frames.publish(payload)
        payload[0] = 0
        self.assertEqual(frames.wait_next(0), (2, b"latest"))
        self.assertIsNone(frames.wait_next(2, timeout=0.01))

    def test_close_wakes_waiter(self):
        frames = LatestFrame()
        result = []
        waiter = threading.Thread(target=lambda: result.append(frames.wait_next(0)))
        waiter.start()
        frames.close()
        waiter.join(timeout=1)
        self.assertFalse(waiter.is_alive())
        self.assertEqual(result, [None])
        frames.publish(b"ignored after close")
        self.assertEqual(frames.snapshot()[0]["sequence"], 0)


class CameraStreamTests(unittest.TestCase):
    def setUp(self):
        self.server = CameraStreamServer(port=0, max_viewers=2)
        self.server.start()
        self.clients = []

    def tearDown(self):
        for client in self.clients:
            client.close()
        self.server.stop()
        self.assertFalse(self.server.thread.is_alive())

    def request(self, path, method="GET"):
        client = http.client.HTTPConnection("127.0.0.1", self.server.port, timeout=2)
        self.clients.append(client)
        client.request(method, path)
        return client.getresponse()

    def test_html_page_and_no_file_server(self):
        response = self.request("/")
        self.assertEqual(response.status, 200)
        self.assertIn(b"/stream.mjpg", response.read())
        for path in ("/vlm_worker.py", "/best.pt", "/../vlm_worker.py"):
            response = self.request(path)
            self.assertEqual(response.status, 404)
            response.read()
        response = self.request("/", "POST")
        self.assertEqual(response.status, 501)
        response.read()

    def test_no_frame_is_unavailable(self):
        response = self.request("/health")
        self.assertEqual(response.status, 503)
        self.assertFalse(json.loads(response.read())["ready"])
        for path in ("/snapshot.jpg", "/stream.mjpg"):
            response = self.request(path)
            self.assertEqual(response.status, 503)
            response.read()

    def test_health_and_snapshot(self):
        self.server.publish(b"jpeg-payload")
        response = self.request("/health")
        self.assertEqual(response.status, 200)
        state = json.loads(response.read())
        self.assertTrue(state["ready"])
        self.assertEqual(state["sequence"], 1)
        response = self.request("/snapshot.jpg?t=123")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Content-Type"), "image/jpeg")
        self.assertEqual(response.getheader("Cache-Control"), "no-store")
        self.assertEqual(response.read(), b"jpeg-payload")

    def read_part(self, response):
        self.assertEqual(response.readline(), b"--frame\r\n")
        headers = {}
        while True:
            line = response.readline()
            if line == b"\r\n":
                break
            self.assertTrue(line, "Unexpected end of MJPEG stream")
            name, value = line.decode().split(":", 1)
            headers[name.lower()] = value.strip()
        payload = response.read(int(headers["content-length"]))
        self.assertEqual(response.read(2), b"\r\n")
        return headers, payload

    def test_two_viewers_share_frames_and_limit_is_enforced(self):
        self.server.publish(b"jpeg-one")
        first = self.request("/stream.mjpg")
        second = self.request("/stream.mjpg")
        for response in (first, second):
            self.assertEqual(response.status, 200)
            self.assertIn("boundary=frame", response.getheader("Content-Type"))
            headers, payload = self.read_part(response)
            self.assertEqual(headers["x-frame-sequence"], "1")
            self.assertEqual(payload, b"jpeg-one")
        extra = self.request("/stream.mjpg")
        self.assertEqual(extra.status, 503)
        extra.read()
        self.server.publish(b"jpeg-two")
        for response in (first, second):
            headers, payload = self.read_part(response)
            self.assertEqual(headers["x-frame-sequence"], "2")
            self.assertEqual(payload, b"jpeg-two")
            response.close()

    def test_stale_frame_is_not_a_live_snapshot(self):
        self.server.frames.stale_after = 0.001
        self.server.publish(b"old-jpeg")
        time.sleep(0.01)
        response = self.request("/health")
        self.assertEqual(response.status, 503)
        self.assertFalse(json.loads(response.read())["ready"])
        response = self.request("/snapshot.jpg")
        self.assertEqual(response.status, 503)
        response.read()

    def test_camera_stall_ends_open_stream(self):
        self.server.frames.stale_after = 0.2
        self.server.publish(b"last-frame")
        response = self.request("/stream.mjpg")
        self.read_part(response)
        self.assertEqual(response.read(), b"")


class CameraCliTests(unittest.TestCase):
    def run_cli(self, *args):
        script = Path(__file__).resolve().parents[1] / "human_detect.py"
        return subprocess.run(
            [sys.executable, "-S", str(script), *args],
            capture_output=True, timeout=5,
        )

    def test_help_works_without_camera_dependencies(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"--stream-source", result.stdout)
        self.assertIn(b"--headless", result.stdout)

    def test_invalid_settings_fail_before_opening_camera(self):
        for option, value in (("--stream-fps", "0"), ("--stream-port", "65536"),
                              ("--stream-quality", "100"), ("--stream-width", "abc")):
            result = self.run_cli(option, value)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn(b"ModuleNotFoundError", result.stderr)


if __name__ == "__main__":
    unittest.main()
