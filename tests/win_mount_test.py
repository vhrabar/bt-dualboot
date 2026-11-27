import os

import pytest

from bt_dualboot import win_mount
from bt_dualboot.windows_registry import WINDOWS10_REGISTRY_PATH


def encode_mount_point(path):
    """Encodes a path the way the kernel writes it into /proc/mounts"""
    return (
        path.replace("\\", "\\134").replace(" ", "\\040").replace("\t", "\\011").replace("\n", "\\012")
    )


@pytest.fixture
def proc_mounts(tmp_path, monkeypatch):
    """Writes a fake /proc/mounts from (source, mount_point) pairs"""

    def write(entries):
        proc_mounts_path = tmp_path / "proc_mounts"
        lines = [
            f"{source} {encode_mount_point(mount_point)} ntfs3 rw,relatime 0 0\n"
            for source, mount_point in entries
        ]
        proc_mounts_path.write_text("".join(lines))
        monkeypatch.setattr(win_mount, "PROC_MOUNTS", str(proc_mounts_path))

    return write


def make_windows_partition(path):
    registry = os.path.join(path, WINDOWS10_REGISTRY_PATH)
    os.makedirs(os.path.dirname(registry))
    open(registry, "w").close()
    return str(path)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("/media/user/Windows", "/media/user/Windows"),
        ("/media/user/Windows\\040Drive", "/media/user/Windows Drive"),
        ("/media/user/a\\011b", "/media/user/a\tb"),
        ("/media/user/a\\012b", "/media/user/a\nb"),
        ("/media/user/back\\134slash", "/media/user/back\\slash"),
        # an escaped backslash followed by digits must not be decoded twice
        ("/media/user/x\\134040", "/media/user/x\\040"),
    ],
)
def test_decode_mount_point(raw, expected):
    assert win_mount.decode_mount_point(raw) == expected


def test_mounts_to_try_skips_loop_and_non_dev_sources(proc_mounts):
    proc_mounts(
        [
            ("/dev/nvme0n1p3", "/media/user/Windows Drive"),
            ("/dev/loop0", "/snap/core/1"),
            ("tmpfs", "/run"),
            ("proc", "/proc"),
            ("/dev/sda1", "/"),
        ]
    )

    assert win_mount.mounts_to_try() == ["/media/user/Windows Drive", "/"]


@pytest.mark.parametrize(
    "label", ["Windows", "Windows Drive", "Windows\tTab", "Windows [C]", "back\\slash"]
)
def test_locate_windows_mount_points(label, tmp_path, proc_mounts):
    """#29: Windows partitions are found whatever characters their mount point has"""
    windows = make_windows_partition(tmp_path / label)
    other = tmp_path / "Data Disk"
    other.mkdir()
    proc_mounts([("/dev/nvme0n1p3", windows), ("/dev/sda1", str(other))])

    assert win_mount.locate_windows_mount_points() == [windows]


def test_locate_windows_mount_points_several(tmp_path, proc_mounts):
    first = make_windows_partition(tmp_path / "Windows 10")
    second = make_windows_partition(tmp_path / "Windows 11")
    proc_mounts([("/dev/sda2", first), ("/dev/sdb2", second)])

    assert win_mount.locate_windows_mount_points() == [first, second]


def test_locate_windows_mount_points_none(tmp_path, proc_mounts):
    proc_mounts([("/dev/sda1", str(tmp_path))])

    assert win_mount.locate_windows_mount_points() == []
