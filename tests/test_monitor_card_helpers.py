"""Unit tests for the pure helpers in monitor card UI (no GTK required)."""

from hyprmod.pages.monitors.card import (
    CM_MODES,
    CM_VALUES,
    SDR_VALUE_DEFAULT,
    _format_sdr,
    _parse_sdr,
)


class TestParseSdr:
    def test_none_returns_default(self):
        assert _parse_sdr(None) == SDR_VALUE_DEFAULT

    def test_numeric_string(self):
        assert _parse_sdr("1.25") == 1.25

    def test_zero(self):
        assert _parse_sdr("0") == 0.0

    def test_invalid_falls_back_to_default(self):
        assert _parse_sdr("not a number") == SDR_VALUE_DEFAULT


class TestFormatSdr:
    def test_default_returns_none(self):
        assert _format_sdr(SDR_VALUE_DEFAULT) is None

    def test_near_default_returns_none(self):
        # Float-precision jitter around 1.0 — still treated as "default".
        assert _format_sdr(1.0 + 1e-9) is None
        assert _format_sdr(1.0 - 1e-9) is None

    def test_just_below_default_emits_value(self):
        # 0.95 is a valid override the spinner can produce; it must not be swallowed.
        assert _format_sdr(0.95) == "0.95"

    def test_override_formatted(self):
        assert _format_sdr(1.2) == "1.2"

    def test_trailing_zero_stripped(self):
        assert _format_sdr(1.5) == "1.5"
        assert _format_sdr(0.8) == "0.8"

    def test_two_decimal_places(self):
        assert _format_sdr(0.98) == "0.98"

    def test_zero_renders_as_zero(self):
        # Regression: naive rstrip("0").rstrip(".") would produce "" for 0.0,
        # which then got written as a malformed config line.
        assert _format_sdr(0.0) == "0"


class TestColorManagementPresets:
    def test_aligned_lengths(self):
        assert len(CM_MODES) == len(CM_VALUES)

    def test_first_value_is_none(self):
        # The first entry represents "no override" / Hyprland default.
        assert CM_VALUES[0] is None

    def test_hdr_presets_present(self):
        assert "hdr" in CM_VALUES
        assert "hdredid" in CM_VALUES

    def test_standard_presets_present(self):
        for preset in ("srgb", "adobe", "wide", "edid"):
            assert preset in CM_VALUES
