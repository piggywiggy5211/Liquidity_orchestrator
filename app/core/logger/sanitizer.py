import re
from typing import List, Callable

# IBAN regex: starts with 2 letters, 2 digits, then 11-27 alphanumeric characters
IBAN_REGEX = re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,27}\b')


def mask_iban(text: str) -> str:
    """Masks IBAN numbers in the given text."""
    def replace(match):
        iban = match.group(0)
        return f"{iban[:4]}****{iban[-4:]}"

    return IBAN_REGEX.sub(replace, text)


class LogSanitizer:
    def __init__(self):
        self._sanitizers: List[Callable[[str], str]] = [
            mask_iban,
        ]

    def add_sanitizer(self, sanitizer: Callable[[str], str]):
        """Adds a new sanitization function to the list."""
        self._sanitizers.append(sanitizer)

    def sanitize(self, text: str) -> str:
        """Applies all registered sanitizers to the input text."""
        for sanitizer in self._sanitizers:
            text = sanitizer(text)
        return text


# Global sanitizer instance
log_sanitizer = LogSanitizer()
