import re
from typing import Optional


class InputSanitizer:
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"forget\s+(all\s+)?previous",
        r"new\s+instructions\s*:",
        r"system\s*prompt",
        r"---\s*end\s*(of)?\s*prompt",
        r"pretend\s+you\s+are",
        r"act\s+as\s+(if\s+)?you",
        r"bypass\s+(all\s+)?restrictions",
        r"reveal\s+(your|the)\s+(system|instructions|prompt)",
        r"you\s+are\s+now\s+(DAN|jailbroken)",
    ]

    def __init__(self):
        self.patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.INJECTION_PATTERNS
        ]

    def clean(self, text: str) -> str:
        """Remove potentially dangerous delimiters from input."""
        text = re.sub(r'[-]{3,}', '', text)
        text = re.sub(r'[=]{3,}', '', text)
        text = text.replace('{{', '{ {').replace('}}', '} }')
        return text.strip()

    def check(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Check whether the input contains a prompt injection attempt.

        Returns:
            (True, matched pattern) if malicious input is detected.
            (False, None) otherwise.
        """
        for pattern in self.patterns:
            if pattern.search(text):
                return True, pattern.pattern
        return False, None

    def sanitize(self, text: str) -> str:
        """
        Main entry point: clean the text, then check it for injection.
        Raises ValueError if an injection attempt is detected.
        """
        cleaned = self.clean(text)

        is_malicious, matched = self.check(cleaned)
        if is_malicious:
            raise ValueError(f"Prompt injection detected: matched rule '{matched}'")

        return cleaned


class PIIDetector:
    """
    Detect and mask personally identifiable information.
    Works on BOTH input (before LLM) and output (before client).
    """

    PATTERNS = {
        "email": re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),
        "phone": re.compile(
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
        ),
        "ssn": re.compile(
            r"\b\d{3}-\d{2}-\d{4}\b"
        ),
        "credit_card": re.compile(
            r"\b\d{4}(?:[-\s]?\d{4}){3}\b"
        ),
        "api_key": re.compile(
            r"\bapi[_\s]?key\s*(?:is|:|=)?\s*\S+",
            re.IGNORECASE
        ),
        "password": re.compile(
            r"\bpassword\s*(?:is|:|=)\s*\S+",
            re.IGNORECASE
        ),
    }

    MASK_MAP = {
        "email": "[EMAIL REDACTED]",
        "phone": "[PHONE REDACTED]",
        "ssn": "[SSN REDACTED]",
        "credit_card": "[CREDIT CARD REDACTED]",
        "api_key": "[API KEY REDACTED]",
        "password": "[PASSWORD REDACTED]",
    }

    def detect(self, text: str) -> dict:
        """Detect PII patterns and return which types were found."""
        found = {}
        for pii_type, pattern in self.PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                found[pii_type] = matches
        return found

    def mask(self, text: str) -> str:
        """Replace all PII with redaction markers."""
        masked = text
        for pii_type, pattern in self.PATTERNS.items():
            masked = pattern.sub(self.MASK_MAP[pii_type], masked)
        return masked


class OutputValidator:
    """Validate LLM output."""

    HARMFUL_PATTERNS = [
        re.compile(r"here('s| is) (how|the way) to (hack|steal|attack)", re.I),
        re.compile(r"password\s+is\s+", re.I),
    ]

    def __init__(self):
        self.pii_detector = PIIDetector()

    def validate(self, output: str) -> tuple[bool, str, Optional[str]]:
        # Step 1: Detect PII
        pii_found = self.pii_detector.detect(output)
        if pii_found:
            cleaned = self.pii_detector.mask(output)
            return False, cleaned, "PII detected"

        # Step 2: Detect harmful content
        for pattern in self.HARMFUL_PATTERNS:
            if pattern.search(output):
                return False, "[CONTENT BLOCKED]", "Potential harmful content detected"

        # Step 3: Safe output
        return True, output, None


class SecurityPipeline:
    """Complete secure processing pipeline."""

    def __init__(self):
        self.sanitizer = InputSanitizer()
        self.pii_detector = PIIDetector()
        self.validator = OutputValidator()

    def check_input(self, text: str) -> tuple[bool, str, list[str]]:
        """
        Process an incoming request.

        Returns:
            (is_safe, processed_text, warnings)
            - If an injection is detected: (False, "", [reason])
            - Otherwise: (True, cleaned_and_masked_text, [pii warnings])
        """
        warnings: list[str] = []

        # Step 1: Block malicious input
        is_malicious, matched = self.sanitizer.check(text)
        if is_malicious:
            return False, "", [f"Prompt injection detected: matched rule '{matched}'"]
            
        # Step 2: Clean dangerous delimiters
        cleaned = self.sanitizer.clean(text)

        # Step 3: Mask PII if found (mask the cleaned text, not the raw text,
        # so the delimiter cleaning above is preserved)
        pii_found = self.pii_detector.detect(cleaned)
        if pii_found:
            cleaned = self.pii_detector.mask(cleaned)
            warnings.extend(f"PII masked: {pii_type}" for pii_type in pii_found)

        return True, cleaned, warnings

    def check_output(self, text: str) -> tuple[str, list[str]]:
        """
        Validate output before returning to the client.

        Returns:
            (cleaned_output, warnings)
        """
        is_valid, cleaned, reason = self.validator.validate(text)
        warnings = [] if reason is None else [reason]
        return cleaned, warnings




