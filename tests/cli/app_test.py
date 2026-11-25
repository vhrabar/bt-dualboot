import sys
from unittest.mock import Mock

import pytest

from bt_dualboot.bluetooth_device import BluetoothDevice
from bt_dualboot.bt_sync_manager import BtSyncManager
from bt_dualboot.bt_sync_manager import bt_sync_manager as sync_module
from bt_dualboot.cli import app, tools


@pytest.mark.parametrize(
    "mac",
    [
        "ABC",
        "",
        "AABBCCDDEEFF",
        "AA:BB:CC:DD:EE",
        "AA:BB:CC:DD:EE:FF:00",
        "A:BB:CC:DD:EE:FF",
        "AA-BB-CC-DD-EE-FF",
        "AA:BB:CC:DD:EE:GG",
        "AA:BB:CC:DD:EE:FF\n",
        "AA:BB:CC:DD:EE:FF,11:22:33:44:55:66",
    ],
)
def test_sync_rejects_malformed_mac(mac, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["bt-dualboot", "--sync", mac])

    with pytest.raises(SystemExit) as exc_info:
        app.parse_argv()

    assert exc_info.value.code == 2
    assert "MAC address must have the format XX:XX:XX:XX:XX:XX" in capsys.readouterr().err


def test_sync_accepts_multiple_macs_case_insensitively(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["bt-dualboot", "--sync", "aa:bb:cc:dd:ee:ff", "11:22:33:aa:BB:cc", "--no-backup"],
    )

    assert app.parse_argv().sync == ["AA:BB:CC:DD:EE:FF", "11:22:33:AA:BB:CC"]


@pytest.mark.parametrize("dry_run", [False, True])
def test_sync_reports_writes_only_when_performed(dry_run, monkeypatch, capsys):
    mac = "AA:BB:CC:DD:EE:FF"
    linux_device = BluetoothDevice(
        mac=mac, adapter_mac="11:22:33:44:55:66", pairing_key="11" * 16, source="Linux"
    )
    windows_device = BluetoothDevice(
        mac=mac, adapter_mac="11:22:33:44:55:66", pairing_key="22" * 16, source="Windows"
    )
    registry = Mock()
    manager = BtSyncManager(registry)
    monkeypatch.setattr(sync_module, "get_linux_devices", lambda: [linux_device])
    monkeypatch.setattr(sync_module, "get_windows_devices", lambda registry: [windows_device])
    monkeypatch.setattr(app.Application, "_sync_manager", lambda self: manager)
    monkeypatch.setattr(app, "require_chntpw_package", lambda: None)
    args = ["bt-dualboot", "--win", "/test/windows", "--sync", mac.lower(), "--no-backup"]
    if dry_run:
        args.append("--dry-run")
    monkeypatch.setattr(sys, "argv", args)

    app.main()

    stdout, stderr = capsys.readouterr()
    assert stderr == ""
    if dry_run:
        registry.import_dict.assert_not_called()
        assert stdout == f"> DRY RUN: push devices {mac}\n"
        assert "successfully" not in stdout
    else:
        registry.import_dict.assert_called_once()
        assert stdout == f"synced {mac} successfully\n"


@pytest.mark.parametrize("command", ["apt install chntpw", "dnf install chntpw", "pacman -S chntpw"])
def test_missing_reged_shows_package_installation_commands(command, monkeypatch):
    monkeypatch.setattr(tools.shutil, "which", lambda executable: None)

    with pytest.raises(SystemExit) as exc_info:
        tools.require_chntpw_package()

    assert "Missing dependency `reged`" in str(exc_info.value)
    assert f"sudo {command}" in str(exc_info.value)


def test_installed_reged_needs_no_installation_hint(monkeypatch, capsys):
    monkeypatch.setattr(tools.shutil, "which", lambda executable: "/usr/bin/reged")

    tools.require_chntpw_package()

    assert capsys.readouterr() == ("", "")
