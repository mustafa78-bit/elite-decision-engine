import os
from core.validation import (
    ConfigValidator, validate_config, validate_port,
    validate_positive_float, validate_threshold,
    validate_secrets, validate_startup, mask_secret,
)


class TestMaskSecret:

    def test_masks_long(self):
        assert mask_secret("abcdefghijklmnop") == "abcd****mnop"

    def test_masks_short(self):
        assert mask_secret("abc") == "****"

    def test_masks_empty(self):
        assert mask_secret("") == ""

    def test_masks_none(self):
        assert mask_secret(None) == ""


class TestValidateSecrets:

    def test_returns_list(self):
        result = validate_secrets()
        assert isinstance(result, list)


class TestValidateStartup:

    def test_returns_list(self):
        result = validate_startup()
        assert isinstance(result, list)


class TestConfigValidator:

    def test_valid(self):
        v = ConfigValidator()
        assert v.is_valid is True
        assert v.validate() == []

    def test_check_failure(self):
        v = ConfigValidator()
        v.check(False, "test error")
        assert v.is_valid is False
        assert "test error" in v.validate()

    def test_check_success(self):
        v = ConfigValidator()
        v.check(True, "should not appear")
        assert v.is_valid is True


class TestValidators:

    def test_validate_port(self):
        assert validate_port("8080") == 8080

    def test_validate_port_invalid(self):
        import pytest
        with pytest.raises((ValueError, TypeError)):
            validate_port("99999")
        with pytest.raises((ValueError, TypeError)):
            validate_port("0")
        with pytest.raises((ValueError, TypeError)):
            validate_port("-1")

    def test_validate_positive_float(self):
        assert validate_positive_float("10.5") == 10.5

    def test_validate_positive_float_zero(self):
        import pytest
        with pytest.raises((ValueError, TypeError)):
            validate_positive_float("0")

    def test_validate_threshold(self):
        assert validate_threshold("50") == 50.0
        assert validate_threshold("0") == 0.0
        assert validate_threshold("100") == 100.0

    def test_validate_threshold_invalid(self):
        import pytest
        with pytest.raises((ValueError, TypeError)):
            validate_threshold("-1")
        with pytest.raises((ValueError, TypeError)):
            validate_threshold("101")
