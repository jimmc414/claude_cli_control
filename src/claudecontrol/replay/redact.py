"""
Secret detection and redaction for safe tape storage
Identifies and masks passwords, tokens, keys, and other sensitive data
"""

import re
import os
from typing import List, Pattern, Tuple, Optional


# Common secret patterns to detect and redact
SECRET_PATTERNS: List[Tuple[Pattern, str]] = [
    # Password prompts and values
    (re.compile(r'(?i)(password|passwd|pwd)[\s:=]+\S+'), r'\1: ***'),

    # API keys and tokens
    (re.compile(r'(?i)(api[_-]?key|token|secret[_-]?key|access[_-]?token)[\s:=]+[\S]+'), r'\1: ***'),

    # AWS Access Key IDs
    (re.compile(r'AKIA[0-9A-Z]{16}'), 'AKIA***'),

    # AWS Secret Access Keys (40 chars base64)
    (re.compile(r'(?i)aws[_-]?secret[_-]?access[_-]?key[\s:=]+[\S]{40}'), 'aws_secret_access_key: ***'),

    # GitHub tokens
    (re.compile(r'ghp_[a-zA-Z0-9]{36}'), 'ghp_***'),
    (re.compile(r'gho_[a-zA-Z0-9]{36}'), 'gho_***'),
    (re.compile(r'ghs_[a-zA-Z0-9]{36}'), 'ghs_***'),
    (re.compile(r'ghu_[a-zA-Z0-9]{36}'), 'ghu_***'),

    # Generic secrets (be careful not to be too aggressive)
    (re.compile(r'(?i)secret[\s:=]+\S{8,}'), 'secret: ***'),

    # SSH private key headers
    (re.compile(r'-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----'), '-----BEGIN PRIVATE KEY----- ***'),

    # Bearer tokens
    (re.compile(r'(?i)bearer\s+[a-zA-Z0-9\-._~+/]+=*'), 'Bearer ***'),

    # Basic auth in URLs
    (re.compile(r'(https?://)([^:]+):([^@]+)@'), r'\1***:***@'),

    # Credit card numbers (basic pattern)
    (re.compile(r'\b(?:\d[ -]*?){13,19}\b'), '***-CARD-***'),

    # Social Security Numbers (US)
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '***-**-****'),

    # Email passwords in config
    (re.compile(r'(?i)(email|smtp|mail)[_-]?(password|pwd)[\s:=]+\S+'), r'\1_password: ***'),

    # Database connection strings with passwords
    (re.compile(r'(mongodb|mysql|postgresql|redis)://[^:]+:([^@]+)@'), r'\1://***:***@'),

    # JWT tokens
    (re.compile(r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'), 'eyJ***.eyJ***.***'),
]


class SecretRedactor:
    """Configurable secret redaction engine"""

    def __init__(self,
                 patterns: Optional[List[Tuple[Pattern, str]]] = None,
                 enabled: bool = True,
                 custom_patterns: Optional[List[Tuple[str, str]]] = None):
        """
        Initialize redactor with patterns.

        Args:
            patterns: List of (regex, replacement) tuples
            enabled: Whether redaction is enabled
            custom_patterns: Additional patterns as (pattern_str, replacement) tuples
        """
        self.patterns = patterns or SECRET_PATTERNS.copy()
        self.enabled = enabled and os.environ.get('CLAUDECONTROL_REDACT', '1') != '0'

        # Add custom patterns
        if custom_patterns:
            for pattern_str, replacement in custom_patterns:
                self.patterns.append((re.compile(pattern_str), replacement))

    def redact_text(self, text: str) -> Tuple[str, int]:
        """
        Redact secrets from text.

        Returns:
            Tuple of (redacted_text, redaction_count)
        """
        if not self.enabled:
            return text, 0

        redaction_count = 0

        for pattern, replacement in self.patterns:
            text, count = pattern.subn(replacement, text)
            redaction_count += count

        return text, redaction_count

    def redact_bytes(self, data: bytes) -> Tuple[bytes, int]:
        """
        Redact secrets from byte data.

        Returns:
            Tuple of (redacted_bytes, redaction_count)
        """
        if not self.enabled:
            return data, 0

        try:
            text = data.decode('utf-8', errors='ignore')
            redacted_text, count = self.redact_text(text)
            return redacted_text.encode('utf-8'), count
        except Exception:
            # If we can't decode, return as-is
            return data, 0

    def detect_secrets(self, text: str) -> List[Tuple[str, str]]:
        """
        Detect secrets without redacting them.

        Returns:
            List of (secret_type, matched_text) tuples
        """
        secrets = []

        for pattern, replacement in self.patterns:
            matches = pattern.finditer(text)
            for match in matches:
                # Try to identify secret type from pattern
                secret_type = self._identify_secret_type(pattern)
                secrets.append((secret_type, match.group(0)))

        return secrets

    def _identify_secret_type(self, pattern: Pattern) -> str:
        """Identify the type of secret from pattern"""
        pattern_str = pattern.pattern.lower()

        if 'password' in pattern_str or 'pwd' in pattern_str:
            return 'password'
        elif 'api' in pattern_str and 'key' in pattern_str:
            return 'api_key'
        elif 'token' in pattern_str:
            return 'token'
        elif 'aws' in pattern_str:
            return 'aws_credential'
        elif 'gh' in pattern_str or 'github' in pattern_str:
            return 'github_token'
        elif 'ssh' in pattern_str or 'private key' in pattern_str:
            return 'ssh_key'
        elif 'bearer' in pattern_str:
            return 'bearer_token'
        elif 'credit' in pattern_str or 'card' in pattern_str:
            return 'credit_card'
        elif 'ssn' in pattern_str or 'social' in pattern_str:
            return 'ssn'
        elif 'jwt' in pattern_str or 'eyj' in pattern_str:
            return 'jwt'
        else:
            return 'secret'


def redact_exchange(exchange: dict, redactor: Optional[SecretRedactor] = None) -> Tuple[dict, dict]:
    """
    Redact secrets from an exchange dict.

    Returns:
        Tuple of (redacted_exchange, redaction_metadata)
    """
    if redactor is None:
        redactor = SecretRedactor()

    redaction_metadata = {
        'redacted': False,
        'count': 0,
        'locations': []
    }

    # Redact input text
    if 'input' in exchange and 'dataText' in exchange['input']:
        original = exchange['input']['dataText']
        redacted, count = redactor.redact_text(original)
        if count > 0:
            exchange['input']['dataText'] = redacted
            redaction_metadata['count'] += count
            redaction_metadata['locations'].append('input.dataText')

    # Redact output chunks
    if 'output' in exchange and 'chunks' in exchange['output']:
        for i, chunk in enumerate(exchange['output']['chunks']):
            if 'dataB64' in chunk:
                import base64
                try:
                    data = base64.b64decode(chunk['dataB64'])
                    redacted_data, count = redactor.redact_bytes(data)
                    if count > 0:
                        chunk['dataB64'] = base64.b64encode(redacted_data).decode('ascii')
                        redaction_metadata['count'] += count
                        redaction_metadata['locations'].append(f'output.chunks[{i}]')
                except Exception:
                    pass

    # Redact environment variables
    if 'meta' in exchange and 'env' in exchange['meta']:
        for key in list(exchange['meta']['env'].keys()):
            if any(secret_key in key.lower() for secret_key in ['password', 'token', 'key', 'secret']):
                exchange['meta']['env'][key] = '***'
                redaction_metadata['count'] += 1
                redaction_metadata['locations'].append(f'meta.env.{key}')

    if redaction_metadata['count'] > 0:
        redaction_metadata['redacted'] = True

    return exchange, redaction_metadata


# Global default redactor instance
_default_redactor = None


def get_default_redactor() -> SecretRedactor:
    """Get or create the default redactor instance"""
    global _default_redactor
    if _default_redactor is None:
        _default_redactor = SecretRedactor()
    return _default_redactor


def redact_text(text: str) -> str:
    """Convenience function for quick text redaction"""
    redactor = get_default_redactor()
    redacted, _ = redactor.redact_text(text)
    return redacted


def redact_bytes(data: bytes) -> bytes:
    """Convenience function for quick bytes redaction"""
    redactor = get_default_redactor()
    redacted, _ = redactor.redact_bytes(data)
    return redacted