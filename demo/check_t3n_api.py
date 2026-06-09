import sys
from pathlib import Path
import argparse

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.terminal3_api_client import validate_configured_identity


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Terminal 3 HTTP token/DID endpoint.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when Terminal 3 rejects the token.")
    args = parser.parse_args()

    load_dotenv()
    result = validate_configured_identity()
    print("Terminal 3 API check")
    print(f"  status       : {result.get('status')}")
    print(f"  api_ok       : {result.get('ok')}")
    print(f"  did_returned : {bool(result.get('did'))}")
    print(f"  did_matches  : {result.get('did_matches')}")
    if result.get("error"):
        print(f"  error        : {result.get('error')}")
    if not result.get("ok"):
        print("  note         : HTTP API credential check failed; local T3N token proof demo is separate.")
    return 0 if result.get("ok") or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
