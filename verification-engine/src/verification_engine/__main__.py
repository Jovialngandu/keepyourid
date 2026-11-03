import argparse
import json
import os

from verification_engine.engine import verify_credential


def _read_credential_value(value: str):
    if value.startswith("{") or value.startswith("["):
        return json.loads(value)
    if os.path.exists(value):
        with open(value, "r", encoding="utf-8") as handle:
            text = handle.read().strip()
        if text.startswith("{") or text.startswith("["):
            return json.loads(text)
        return text
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a signed credential independently from the backend issuer services.")
    parser.add_argument("credential", help="JWS string or JSON file containing a signed credential")
    parser.add_argument("--resolver-url", default=os.getenv("DID_RESOLVER_URL", "https://dev.uniresolver.io"), help="DID resolver endpoint")
    args = parser.parse_args()

    result = verify_credential(_read_credential_value(args.credential), resolver_url=args.resolver_url)
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
