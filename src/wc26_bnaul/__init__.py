#!/usr/bin/env python3
"""
wc26-bnaul — ClawCup Agent for FIFA World Cup 2026
AI agent dự đoán kết quả World Cup 2026 qua ClawCup API
"""

import argparse
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
import urllib.request

BASE_URL = "https://clawcup.io"
API_BASE = f"{BASE_URL}/api/v1"


def get_credentials():
    """Lấy token và signing secret từ environment variables."""
    token = os.environ.get("CLAWCUP_TOKEN")
    secret = os.environ.get("CLAWCUP_SIGNING_SECRET")
    if not token:
        print("Error: CLAWCUP_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    if not secret:
        print("Error: CLAWCUP_SIGNING_SECRET not set", file=sys.stderr)
        sys.exit(1)
    return token, secret


def sign_request(method: str, path: str, body_bytes: bytes, secret: str) -> dict:
    """
    Tạo HMAC signature theo spec ClawCup.
    canonical = METHOD\npath\nts\nnonce\nsha256(body)
    """
    ts = str(int(time.time()))
    nonce = secrets.token_urlsafe(24)
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    canonical = f"{method}\n{path}\n{ts}\n{nonce}\n{body_hash}"
    sig = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    return {
        "X-WCA-Timestamp": ts,
        "X-WCA-Nonce": nonce,
        "X-WCA-Signature": sig,
    }


def api_request(method: str, path: str, body: dict = None) -> dict:
    """Gửi request đã signed tới ClawCup API."""
    token, secret = get_credentials()
    url = f"{API_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body_bytes = b""
    if body is not None:
        body_bytes = json.dumps(body, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        sign_headers = sign_request(method, path, body_bytes, secret)
        headers.update(sign_headers)

    req = urllib.request.Request(url, data=body_bytes if body_bytes else None, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"API Error: {e.code} {e.reason}", file=sys.stderr)
        print(f"Response: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"API Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_me():
    """Hiển thị thông tin agent."""
    data = api_request("GET", "/me")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_fixtures(status: str = "open"):
    """Liệt kê các trận đấu."""
    data = api_request("GET", f"/fixtures?status={status}")
    matches = data.get("matches", [])
    if not matches:
        print("No matches found.")
        return

    print(f"{'Match ID':<10} {'Round':<14} {'Home':<20} {'Away':<20} {'Kickoff (UTC)':<20}")
    print("-" * 90)
    for m in matches:
        kickoff = m.get("kickoff_utc", "N/A")
        print(
            f"{m['match_id']:<10} {m.get('round','?'):<14} "
            f"{m['home']:<20} {m['away']:<20} {kickoff:<20}"
        )


def cmd_predict(match_id: str, pick: str, reasoning: str, exact_score: str = None, probabilities: list = None, binary: bool = False):
    """Gửi dự đoán cho một trận đấu."""
    payload = {
        "match_id": match_id,
        "reasoning": reasoning,
    }

    if binary:
        payload["format"] = "binary"

    if probabilities:
        payload["p"] = probabilities
    elif pick:
        payload["pick"] = pick

    if exact_score:
        payload["exact_score"] = exact_score

    # Sort payload keys to match the JSON serialization used for signing
    payload = dict(sorted(payload.items()))

    print(f"Submitting prediction for {match_id}...")
    data = api_request("POST", "/predictions", payload)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_mine():
    """Hiển thị các dự đoán của agent."""
    data = api_request("GET", "/predictions/mine")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        prog="wc26-bnaul",
        description="ClawCup Agent — FIFA World Cup 2026 AI Predictor"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # me
    sub.add_parser("me", help="Show agent info")

    # fixtures
    p_fix = sub.add_parser("fixtures", help="List matches")
    p_fix.add_argument("--status", default="open", choices=["open", "closed", "all"])

    # predict
    p_pred = sub.add_parser("predict", help="Submit a prediction")
    p_pred.add_argument("match_id", help="Match ID (e.g. m001)")
    p_pred.add_argument("--pick", choices=["HOME", "DRAW", "AWAY"], help="Pick (1X2)")
    p_pred.add_argument("--prob", nargs=3, type=float, metavar=("H", "D", "A"),
                        help="Probabilities [home draw away] (sum=1)")
    p_pred.add_argument("--binary", nargs=2, type=float, metavar=("H", "A"),
                        help="Knockout advance probabilities [home away] (sum=1)")
    p_pred.add_argument("--reasoning", required=True, help="Reasoning (max 16000 chars)")
    p_pred.add_argument("--score", help="Exact scoreline e.g. 2-1")

    # mine
    sub.add_parser("mine", help="Show my predictions")

    args = parser.parse_args()

    if args.command == "me":
        cmd_me()
    elif args.command == "fixtures":
        cmd_fixtures(args.status)
    elif args.command == "predict":
        pick = args.pick
        probs = None
        is_binary = False

        if args.binary:
            is_binary = True
            probs = list(args.binary)
            if abs(sum(probs) - 1.0) > 0.001:
                print("Error: probabilities must sum to 1.0", file=sys.stderr)
                sys.exit(1)
            if args.pick and args.pick == "DRAW":
                print("Error: knockout (binary) cannot have DRAW pick", file=sys.stderr)
                sys.exit(1)
        elif args.prob:
            probs = list(args.prob)
            if abs(sum(probs) - 1.0) > 0.001:
                print("Error: probabilities must sum to 1.0", file=sys.stderr)
                sys.exit(1)

        if not pick and not probs:
            print("Error: must provide --pick or --prob/--binary", file=sys.stderr)
            sys.exit(1)

        cmd_predict(args.match_id, pick, args.reasoning, args.score, probabilities=probs, binary=is_binary)
    elif args.command == "mine":
        cmd_mine()


if __name__ == "__main__":
    main()
