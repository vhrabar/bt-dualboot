import sys
from unittest.mock import Mock

import pytest

from bt_dualboot.bluetooth_device import BluetoothDevice
from bt_dualboot.bt_sync_manager import BtSyncManager
from bt_dualboot.bt_sync_manager import bt_sync_manager as sync_module
from bt_dualboot.cli import app, tools
from bt_dualboot.windows_registry import RegistryError


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


@pytest.fixture
def windows_mounts(monkeypatch):
    """Fakes the auto-discovered Windows mount points"""

    def set_mounts(mount_points):
        locate = lambda: list(mount_points)  # noqa: E731
        monkeypatch.setattr(app, "locate_windows_mount_points", locate)
        monkeypatch.setattr(tools, "locate_windows_mount_points", locate)
        monkeypatch.setattr(app, "require_chntpw_package", lambda: None)

    return set_mounts


@pytest.mark.parametrize(
    "mount_points",
    [[], ["/media/user/Windows"], ["/media/user/Windows 10", "/media/user/Windows 11"]],
)
def test_list_win_mounts_lists_any_number_of_locations(
    mount_points, windows_mounts, monkeypatch, capsys
):
    """--list-win-mounts exits 0 with 0, 1 or 2 Windows mounts and lists them all"""
    windows_mounts(mount_points)
    monkeypatch.setattr(sys, "argv", ["bt-dualboot", "--list-win-mounts"])

    app.main()

    stdout = capsys.readouterr().out
    for mount_point in mount_points:
        assert f" {mount_point}\n" in stdout
    if mount_points == []:
        assert "No Windows partitions found" in stdout


@pytest.mark.parametrize("mount_points", [[], ["/media/user/Windows 10", "/media/user/Windows 11"]])
@pytest.mark.parametrize("command", [["-l"], ["--sync-all", "--no-backup"], ["--sync-all", "--backup"]])
def test_commands_need_univocal_windows_location(mount_points, command, windows_mounts, monkeypatch):
    """-l, --sync, --sync-all and --backup still error when the location is ambiguous"""
    windows_mounts(mount_points)
    monkeypatch.setattr(sys, "argv", ["bt-dualboot", *command])

    with pytest.raises(SystemExit) as exc_info:
        app.main()

    assert "Windows locations found, use `--win MOUNT`" in str(exc_info.value.code)


def run_sync_with_failing_import(monkeypatch, error):
    mac = "AA:BB:CC:DD:EE:FF"
    linux_device = BluetoothDevice(
        mac=mac, adapter_mac="11:22:33:44:55:66", pairing_key="11" * 16, source="Linux"
    )
    windows_device = BluetoothDevice(
        mac=mac, adapter_mac="11:22:33:44:55:66", pairing_key="22" * 16, source="Windows"
    )
    registry = Mock()
    registry.import_dict.side_effect = error
    manager = BtSyncManager(registry)
    monkeypatch.setattr(sync_module, "get_linux_devices", lambda: [linux_device])
    monkeypatch.setattr(sync_module, "get_windows_devices", lambda registry: [windows_device])
    monkeypatch.setattr(app.Application, "_sync_manager", lambda self: manager)
    monkeypatch.setattr(app, "require_chntpw_package", lambda: None)
    argv = ["bt-dualboot", "--win", "/test/windows", "--sync", mac, "--no-backup"]
    monkeypatch.setattr(sys, "argv", argv)
    app.main()


def test_registry_error_is_reported_without_traceback(monkeypatch, capsys):
    """#31: no traceback, non-zero exit, "Nothing changed." and hints"""
    monkeypatch.delenv("DEBUG", raising=False)
    error = RegistryError("The Windows registry /test/windows/SYSTEM is read-only.")

    with pytest.raises(SystemExit) as exc_info:
        run_sync_with_failing_import(monkeypatch, error)

    message = exc_info.value.code
    assert isinstance(message, str), "SystemExit with a message exits with status 1"
    assert message.startswith("ERROR: The Windows registry /test/windows/SYSTEM is read-only.\nNothing changed.")
    assert "Fast Startup" in message
    assert "DEBUG=1" in message
    assert "successfully" not in capsys.readouterr().out


def test_registry_error_keeps_traceback_with_debug(monkeypatch):
    """#31: DEBUG=1 re-raises the original RegistryError"""
    monkeypatch.setenv("DEBUG", "1")

    with pytest.raises(RegistryError, match="read-only"):
        run_sync_with_failing_import(monkeypatch, RegistryError("read-only"))
