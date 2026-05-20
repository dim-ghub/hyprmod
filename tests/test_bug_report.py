"""Tests for the GitHub bug-report URL builder."""

from pathlib import Path
from urllib.parse import ParseResult, parse_qs, urlparse

from hyprmod.core import config
from hyprmod.core.bug_report import (
    ISSUE_URL,
    REPO_URL,
    _classify_install,
    _scrub_user,
    build_bug_report_url,
    detect_install_source,
    hyprmod_version,
)


def _parse(url: str) -> tuple[ParseResult, dict[str, str]]:
    parsed = urlparse(url)
    query = {k: v[0] for k, v in parse_qs(parsed.query, keep_blank_values=True).items()}
    return parsed, query


class TestUrlShape:
    def test_uses_new_issue_endpoint(self, gui_conf_tmp):
        url = build_bug_report_url()
        parsed, _ = _parse(url)
        assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == f"{ISSUE_URL}/new"

    def test_constants_consistent(self):
        assert ISSUE_URL == f"{REPO_URL}/issues"


class TestBody:
    def test_environment_block_present(self, gui_conf_tmp):
        url = build_bug_report_url(running_hyprland_version="0.55.1")
        _, query = _parse(url)
        body = query["body"]
        assert "**Environment**" in body
        assert "- HyprMod:" in body
        assert "- Hyprland (running): 0.55.1" in body
        assert "- Hyprland schema (bundled):" in body
        assert "- Config language: Hyprlang" in body
        assert str(gui_conf_tmp) in body

    def test_offline_hyprland_shown_as_not_detected(self, gui_conf_tmp):
        url = build_bug_report_url(running_hyprland_version=None)
        _, query = _parse(url)
        assert "- Hyprland (running): not detected" in query["body"]

    def test_running_version_v_prefix_stripped(self, gui_conf_tmp):
        url = build_bug_report_url(running_hyprland_version="v0.55.1")
        _, query = _parse(url)
        assert "- Hyprland (running): 0.55.1" in query["body"]

    def test_body_extra_rendered_above_environment(self, gui_conf_tmp):
        url = build_bug_report_url(body_extra="Monitor config failed")
        _, query = _parse(url)
        body = query["body"]
        assert body.index("Monitor config failed") < body.index("**Environment**")

    def test_empty_body_extra_omits_separator(self, gui_conf_tmp):
        url = build_bug_report_url(body_extra="")
        _, query = _parse(url)
        assert "\n---\n" not in query["body"]


class TestTitle:
    def test_nonempty_title_gets_bug_tag(self, gui_conf_tmp):
        url = build_bug_report_url(title='keyword "windowrulev2" rejected')
        _, query = _parse(url)
        assert query["title"] == '[Bug] keyword "windowrulev2" rejected'

    def test_empty_title_has_no_tag(self, gui_conf_tmp):
        url = build_bug_report_url(title="")
        _, query = _parse(url)
        assert query["title"] == ""

    def test_long_title_truncated_with_ellipsis(self, gui_conf_tmp):
        long = "keyword rejected: " + "x" * 200
        url = build_bug_report_url(title=long)
        _, query = _parse(url)
        assert query["title"].startswith("[Bug] ")
        assert len(query["title"]) <= 120
        assert query["title"].endswith("…")

    def test_short_title_untouched_apart_from_tag(self, gui_conf_tmp):
        url = build_bug_report_url(title="Bind failed")
        _, query = _parse(url)
        assert query["title"] == "[Bug] Bind failed"

    def test_title_clipped_to_first_line(self, gui_conf_tmp):
        url = build_bug_report_url(title="invalid mode\ndetails on next line")
        _, query = _parse(url)
        assert query["title"] == "[Bug] invalid mode"

    def test_full_message_still_in_body(self, gui_conf_tmp):
        long = "Window rule failed: " + "y" * 200
        url = build_bug_report_url(title="rejected", body_extra=long)
        _, query = _parse(url)
        assert long in query["body"]


class TestEncoding:
    def test_special_chars_in_title_encoded(self, gui_conf_tmp):
        url = build_bug_report_url(title="Failed: foo & bar = baz")
        _, query = _parse(url)
        assert query["title"] == "[Bug] Failed: foo & bar = baz"

    def test_newlines_in_body_extra_round_trip(self, gui_conf_tmp):
        url = build_bug_report_url(body_extra="line one\nline two")
        _, query = _parse(url)
        assert "line one\nline two" in query["body"]


class TestConfigMode:
    def test_lua_mode_reflected_in_body(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hyprland_config.default_config_dir", lambda: tmp_path)
        (tmp_path / "hyprland.lua").write_text("")
        config.invalidate_lua_mode_cache()
        url = build_bug_report_url()
        _, query = _parse(url)
        assert "- Config language: Lua" in query["body"]


class TestInstallDetection:
    def test_pipx_layout(self):
        p = "/home/u/.local/share/pipx/venvs/hyprmod/lib/python3.12/site-packages/hyprmod"
        assert _classify_install(p, in_venv=True) == "pipx"

    def test_uv_tool_layout(self):
        p = "/home/u/.local/share/uv/tools/hyprmod/lib/python3.12/site-packages/hyprmod"
        assert _classify_install(p, in_venv=True) == "uv tool"

    def test_source_checkout_not_in_site_packages(self):
        assert _classify_install("/home/u/src/hyprmod/hyprmod", in_venv=True) == "source checkout"

    def test_distro_package_in_base_site_packages(self):
        p = "/usr/lib/python3.12/site-packages/hyprmod"
        assert _classify_install(p, in_venv=False) == "system package"

    def test_unrecognized_venv_is_unknown(self):
        p = "/home/u/myenv/lib/python3.12/site-packages/hyprmod"
        assert _classify_install(p, in_venv=True) == "unknown"

    def test_detect_returns_known_label(self):
        # Whatever the test environment is, the label must be one we render.
        assert detect_install_source() in {
            "pipx",
            "uv tool",
            "source checkout",
            "system package",
            "unknown",
        }

    def test_install_method_and_path_in_body(self, gui_conf_tmp):
        url = build_bug_report_url()
        _, query = _parse(url)
        body = query["body"]
        assert f"- HyprMod: {hyprmod_version()} (" in body
        assert "- Install path: `" in body


class TestUsernameScrub:
    def test_username_segment_replaced(self):
        assert _scrub_user("/opt/ivo/venv/hyprmod", "ivo") == "/opt/<user>/venv/hyprmod"

    def test_symlinked_home_path_scrubbed(self):
        assert _scrub_user("/data/ivo/src/hyprmod", "ivo") == "/data/<user>/src/hyprmod"

    def test_substring_not_over_redacted(self):
        assert _scrub_user("~/projects/ivory/hyprmod", "ivo") == "~/projects/ivory/hyprmod"

    def test_collapsed_home_path_unchanged(self):
        path = "~/PycharmProjects/hyprmod/hyprmod"
        assert _scrub_user(path, "ivo") == path

    def test_system_path_unchanged(self):
        path = "/usr/lib/python3.12/site-packages/hyprmod"
        assert _scrub_user(path, "ivo") == path

    def test_empty_username_is_noop(self):
        assert _scrub_user("/data/ivo/hyprmod", "") == "/data/ivo/hyprmod"

    def test_report_scrubs_out_of_home_username(self, gui_conf_tmp, monkeypatch):
        user = Path.home().name
        monkeypatch.setattr(
            "hyprmod.core.bug_report.running_package_dir",
            lambda: Path(f"/opt/{user}/venv/lib/python3.12/site-packages/hyprmod"),
        )
        url = build_bug_report_url()
        _, query = _parse(url)
        install_line = next(
            ln for ln in query["body"].splitlines() if ln.startswith("- Install path:")
        )
        assert "<user>" in install_line
        assert f"/{user}/" not in install_line


class TestPrivacy:
    def test_config_path_collapsed_to_tilde(self, tmp_path, monkeypatch):
        monkeypatch.setattr("hyprland_config.default_config_dir", lambda: tmp_path)
        config.invalidate_lua_mode_cache()
        in_home = Path.home() / ".config/hypr/hyprland-gui.conf"
        monkeypatch.setattr(config, "managed_path", lambda: in_home)
        url = build_bug_report_url()
        _, query = _parse(url)
        assert "`~/.config/hypr/hyprland-gui.conf`" in query["body"]
        assert str(Path.home()) not in query["body"]
