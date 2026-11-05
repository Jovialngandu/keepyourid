
from datetime import datetime, timezone


def verify_expiration(credential: dict) -> tuple[bool, str | None]:
    valid_from = credential.get("validFrom")
    valid_until = credential.get("validUntil")

    if not valid_from:
        return False, "Missing validFrom."

    try:
        start = datetime.fromisoformat(
            valid_from.replace("Z", "+00:00")
        )

        if start.tzinfo is None:
            return False, "validFrom must include a timezone."

        now = datetime.now(timezone.utc)

        if start > now:
            return False, "Credential is not valid yet."

        if valid_until:
            end = datetime.fromisoformat(
                valid_until.replace("Z", "+00:00")
            )

            if end.tzinfo is None:
                return False, "validUntil must include a timezone."

            if end <= now:
                return False, "Credential has expired."

            if end <= start:
                return False, "Invalid validity period."

        return True, None

    except (ValueError, TypeError):
        return False, "Invalid credential date format."
