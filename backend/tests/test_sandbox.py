from fastapi.testclient import TestClient

from sandbox.server import app

client = TestClient(app)


def test_runs_code():
    r = client.post("/run", json={"code": "print(2 + 2)"}).json()
    assert r["stdout"].strip() == "4"
    assert r["exit_code"] == 0


def test_timeout():
    r = client.post("/run", json={"code": "while True: pass"}).json()
    assert r["exit_code"] != 0
