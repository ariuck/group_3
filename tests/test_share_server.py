"""결과 주고받기 서버(tools/share_server.py) 시험 — 이 PC 안에서(127.0.0.1) 가짜 파일로 확인한다.

실행 (프로젝트 폴더에서):  python -m unittest tests/test_share_server.py
"""
import http.client
import io
import json
import shutil
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from urllib.parse import quote

from tools import share_server as ss

PIN = "4821"


def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


GOOD = make_zip({"DS1/labels/train/a.txt": "2 0.5 0.5 0.2 0.2\n", "DS1/labels/train/b.txt": "",
                 "검수표_김동훈.csv": "\ufeffNo,이미지 파일명\r\n1,a.jpg\r\n2,b.jpg\r\n"})


class ShareServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.logs = []
        self.server = ss.ShareServer(("127.0.0.1", 0), self.tmp / "공유", PIN, max_mb=1, log=self.logs.append)
        self.port = self.server.server_address[1]
        t = threading.Thread(target=self.server.serve_forever, daemon=True)
        t.start()
        self.addCleanup(lambda: (self.server.shutdown(), self.server.server_close()))

    def call(self, method, path, body=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            c.request(method, path, body=body)
            r = c.getresponse()
            return r.status, r.read(), dict(r.getheaders())
        finally:
            c.close()

    def api(self, method, path, body=None):
        status, data, _h = self.call(method, path, body)
        try:
            return status, json.loads(data.decode("utf-8"))
        except ValueError:
            return status, data

    def upload(self, name, data, pin=PIN):
        return self.api("PUT", f"/api/upload?pin={pin}&name={name}", data)

    # ── 접속 ───────────────────────────────────────────────────────────
    def test_page_is_served_without_a_pin_but_data_needs_it(self):
        status, body, headers = self.call("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("결과 주고받기", body.decode("utf-8"))
        self.assertEqual(self.api("GET", "/api/list")[0], 403)
        self.assertEqual(self.api("GET", "/api/list?pin=0000")[0], 403)
        status, data = self.api("GET", f"/api/list?pin={PIN}")
        self.assertEqual((status, data), (200, {"send": [], "received": []}))

    def test_wrong_pin_locks_the_client_after_several_tries(self):
        for _ in range(ss.MAX_FAILS):
            self.assertEqual(self.api("GET", "/api/list?pin=1111")[0], 403)
        self.assertEqual(self.api("GET", f"/api/list?pin={PIN}")[0], 429)      # 맞는 번호도 잠시 거부

    def test_unknown_paths_are_404(self):
        self.assertEqual(self.api("GET", "/etc/passwd")[0], 404)
        self.assertEqual(self.api("PUT", f"/api/other?pin={PIN}", b"x")[0], 404)

    # ── 내려받기 ────────────────────────────────────────────────────────
    def test_download_lists_and_returns_the_file_from_the_send_folder_only(self):
        (self.server.send_dir / "결과 1.zip").write_bytes(GOOD)
        (self.tmp / "비밀.zip").write_bytes(b"secret")                        # 보내기 폴더 밖
        status, data = self.api("GET", f"/api/list?pin={PIN}")
        self.assertEqual([f["name"] for f in data["send"]], ["결과 1.zip"])
        status, body, headers = self.call("GET", f"/api/download?pin={PIN}&name=%EA%B2%B0%EA%B3%BC%201.zip")
        self.assertEqual((status, body), (200, GOOD))
        self.assertIn("attachment", headers["Content-Disposition"])
        for bad in ("../비밀.zip", "../../비밀.zip", "없음.zip", "x.txt"):
            self.assertEqual(self.api("GET", f"/api/download?pin={PIN}&name={quote(bad, safe='')}")[0], 404, bad)
        self.assertEqual(self.api("GET", "/api/download?name=%EA%B2%B0%EA%B3%BC%201.zip")[0], 403)    # 번호 없이는 안 됨

    # ── 올리기 ─────────────────────────────────────────────────────────
    def test_valid_upload_is_saved_and_unpacked(self):
        status, data = self.upload("%EA%B9%80%EB%8F%99%ED%9B%88.zip", GOOD)       # 김동훈.zip
        self.assertEqual((status, data["saved"], data["labels"], data["rows"]), (200, "김동훈.zip", 2, 2))
        self.assertEqual((self.server.recv_dir / "김동훈.zip").read_bytes(), GOOD)
        unpacked = self.server.unpacked_dir
        self.assertEqual((unpacked / "DS1" / "labels" / "train" / "a.txt").read_text(encoding="utf-8"), "2 0.5 0.5 0.2 0.2\n")
        self.assertTrue((unpacked / "검수표_김동훈.csv").is_file())
        self.assertEqual([p.name for p in self.server.recv_dir.glob("*.part")], [])           # 임시 파일이 남지 않는다
        self.assertEqual(self.api("GET", f"/api/list?pin={PIN}")[1]["received"][0]["name"], "김동훈.zip")

    def test_same_name_is_never_overwritten(self):
        self.upload("a.zip", GOOD)
        status, data = self.upload("a.zip", make_zip({"x.txt": "1 0.1 0.1 0.1 0.1\n"}))
        self.assertEqual(status, 200)
        self.assertNotEqual(data["saved"], "a.zip")
        self.assertEqual((self.server.recv_dir / "a.zip").read_bytes(), GOOD)

    def test_unsafe_or_wrong_files_are_rejected(self):
        cases = {
            "사진이 든 zip": make_zip({"a.jpg": "x", "b.txt": "1 0 0 0 0\n"}),
            "프로그램이 든 zip": make_zip({"run.exe": "x"}),
            "폴더를 벗어나는 경로": make_zip({"../밖.txt": "x"}),
            "절대 경로": make_zip({"/etc/x.txt": "x"}),
            "Zone.Identifier": make_zip({"a.txt:Zone.Identifier": "[ZoneTransfer]"}),
            "zip 이 아님": b"this is not a zip file",
        }
        for label, data in cases.items():
            status, resp = self.upload("x.zip", data)
            self.assertEqual(status, 400, label)
            self.assertIn("error", resp, label)
        self.assertEqual(list(self.server.recv_dir.glob("*.zip")), [])
        self.assertFalse((self.tmp / "밖.txt").exists())
        self.assertFalse((self.server.recv_dir / "밖.txt").exists())

    def test_name_must_be_a_zip_and_folder_parts_are_dropped(self):
        self.assertEqual(self.upload("x.txt", GOOD)[0], 400)
        self.assertEqual(self.upload("", GOOD)[0], 400)
        status, data = self.upload("..%2F..%2F%EC%95%85.zip", GOOD)             # ../../악.zip
        self.assertEqual((status, data["saved"]), (200, "악.zip"))
        self.assertTrue((self.server.recv_dir / "악.zip").is_file())

    def test_too_large_upload_is_refused(self):
        big = make_zip({"a.txt": "0" * 10})
        self.server.max_bytes = 100                                             # 시험용으로 아주 작게
        status, resp = self.upload("big.zip", big + b"\0" * 5000)
        self.assertEqual(status, 413)
        self.assertEqual(list(self.server.recv_dir.glob("*.zip")), [])

    def test_zip_that_expands_too_much_is_refused(self):
        bomb = make_zip({f"{i}.txt": "0" * 1_000_000 for i in range(5)})          # 압축하면 아주 작지만 풀면 5MB (한도: 올리는 크기 한도의 4배 = 4MB)
        status, resp = self.upload("bomb.zip", bomb)
        self.assertEqual(status, 400)
        self.assertEqual(list(self.server.unpacked_dir.rglob("*.txt")), [])

    def test_upload_needs_the_pin(self):
        self.assertEqual(self.upload("a.zip", GOOD, pin="0000")[0], 403)
        self.assertEqual(list(self.server.recv_dir.glob("*.zip")), [])

    # ── 도우미 함수 ────────────────────────────────────────────────────
    def test_helpers(self):
        self.assertEqual(ss.safe_name("../../a b.zip"), "a b.zip")
        self.assertEqual(ss.safe_name("C:\\x\\y.zip"), "y.zip")
        self.assertIsNone(ss.safe_name("a.exe"))
        self.assertIsNone(ss.safe_name(".zip"))
        self.assertTrue(ss.is_local_client("192.168.0.5") and ss.is_local_client("10.1.2.3") and ss.is_local_client("127.0.0.1"))
        self.assertTrue(ss.is_local_client("::ffff:192.168.1.1"))
        self.assertFalse(ss.is_local_client("8.8.8.8"))
        self.assertFalse(ss.is_local_client("not-an-ip"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
