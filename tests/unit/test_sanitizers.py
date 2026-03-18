from app.core.sanitizers.http_saitazer import sanitize_headers
from app.core.sanitizers.log_sanitizer import LogSanitizer, mask_iban


def test_mask_iban():
    iban = "DE12345678901234567890"
    masked = mask_iban(iban)
    assert masked.startswith("DE12")
    assert masked.endswith("7890")
    assert "*" in masked


def test_log_sanitizer_multiple_rules():
    s = LogSanitizer()
    # Add a dummy rule
    s.add_sanitizer(lambda x: x.replace("SECRET", "******"))

    text = "IBAN: DE12345678901234567890 and SECRET value"
    sanitized = s.sanitize(text)

    assert "DE12****7890" in sanitized
    assert "******" in sanitized
    assert "SECRET" not in sanitized


def test_sanitize_headers():
    headers = {"Authorization": "Bearer token123", "Content-Type": "application/json", "authorization": "Secret"}
    sanitized = sanitize_headers(headers)
    assert "Authorization" not in sanitized
    assert "authorization" not in sanitized
    assert sanitized["Content-Type"] == "application/json"
    assert len(sanitized) == 1
