from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8000"


def print_json(label: str, payload: dict) -> None:
    print(label)
    print(json.dumps(payload, indent=2, sort_keys=True))


def wait_for_server(timeout_seconds: float = 30.0) -> None:
    deadline = time.time() + timeout_seconds
    last_error = None
    with httpx.Client(timeout=5.0) as client:
        while time.time() < deadline:
            try:
                response = client.get(f"{BASE_URL}/health")
                if response.status_code == 200:
                    return
                last_error = f"Unexpected health status: {response.status_code}"
            except httpx.HTTPError as exc:
                last_error = str(exc)
            time.sleep(0.5)
    raise RuntimeError(f"Server did not become ready within {timeout_seconds} seconds. Last error: {last_error}")


def start_server() -> subprocess.Popen:
    env = os.environ.copy()
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]
    process = subprocess.Popen(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_server()
    except Exception:
        try:
            output, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()
        raise RuntimeError(f"Failed to start server.\n{output}") from None
    return process


def stop_server(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return

    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def find_target_finding(seed_response: dict) -> int:
    for item in seed_response.get("summaries", []):
        severity = ((item or {}).get("summary") or {}).get("severity")
        if severity in {"major", "contraindicated"}:
            finding_id = item.get("finding_id")
            if finding_id is not None:
                return finding_id
    raise RuntimeError("No finding with severity 'major' or 'contraindicated' was found in the seed response.")


def verify_explanation(payload: dict) -> list[str]:
    errors: list[str] = []

    if payload.get("schema_validation_passed") is not True:
        errors.append("schema_validation_passed is not True")

    if not payload.get("summary"):
        errors.append("summary field is empty")

    if not payload.get("mechanism"):
        errors.append("mechanism field is empty")

    if not payload.get("management"):
        errors.append("management field is empty")

    if payload.get("confidence") not in {"high", "medium", "low"}:
        errors.append("confidence is not one of: high, medium, low")

    return errors


def main() -> int:
    server_process = None
    try:
        server_process = start_server()
        print("Started uvicorn server in the background.")

        with httpx.Client(timeout=120.0) as client:
            seed_response = client.post(f"{BASE_URL}/api/v1/dev/seed")
            seed_payload = seed_response.json()
            print_json("POST /api/v1/dev/seed response:", seed_payload)
            if seed_response.status_code != 200:
                print(f"Seed request failed with status {seed_response.status_code}")
                return 1

            finding_id = find_target_finding(seed_payload)
            print(f"Selected finding_id: {finding_id}")

            explain_response = client.post(f"{BASE_URL}/api/v1/findings/{finding_id}/explain")
            explain_payload = explain_response.json()
            print_json(f"POST /api/v1/findings/{finding_id}/explain response:", explain_payload)
            if explain_response.status_code != 200:
                print(f"Explain request failed with status {explain_response.status_code}")
                return 1

        errors = verify_explanation(explain_payload)
        if errors:
            for error in errors:
                print(error)
            return 1

        print("schema_validation_passed is True")
        print("summary field is not empty")
        print("mechanism field is not empty")
        print("management field is not empty")
        print(f"confidence is valid: {explain_payload['confidence']}")
        return 0
    except Exception as exc:
        print(str(exc))
        return 1
    finally:
        if server_process is not None:
            stop_server(server_process)
            print("Shut down the server.")


if __name__ == "__main__":
    raise SystemExit(main())
