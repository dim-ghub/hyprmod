"""Tests for the XDG install/registration helpers."""

from gi.repository import Gio

from hyprmod import install


class TestIsRegistered:
    def test_returns_true_when_entry_found(self, monkeypatch):
        monkeypatch.setattr(Gio.DesktopAppInfo, "new", staticmethod(lambda _id: object()))
        assert install.is_registered() is True

    def test_returns_false_on_constructor_returned_null(self, monkeypatch):
        # PyGObject turns a NULL return from Gio.DesktopAppInfo.new into a
        # TypeError rather than None; is_registered must treat that as "absent"
        # instead of crashing first launch. https://github.com/BlueManCZ/hyprmod/issues/52
        def _raise(_id):
            raise TypeError("constructor returned NULL")

        monkeypatch.setattr(Gio.DesktopAppInfo, "new", staticmethod(_raise))
        assert install.is_registered() is False
