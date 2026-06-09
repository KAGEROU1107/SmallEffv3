import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.terminal3_api_client import validate_configured_identity


def main() -> int:
    load_dotenv()
    result = validate_configured_identity()
    print("Terminal 3 API check")
    print(f"  status       : {result.get('status')}")
    print(f"  api_ok       : {result.get('ok')}")
    print(f"  did_returned : {bool(result.get('did'))}")
    print(f"  did_matches  : {result.get('did_matches')}")
    if result.get("error"):
        print(f"  error        : {result.get('error')}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
