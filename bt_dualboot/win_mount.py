import glob
import os
import re

from .windows_registry import WINDOWS10_REGISTRY_PATH

PROC_MOUNTS = "/proc/mounts"


def decode_mount_point(raw_mount_point):
    """Decodes octal escapes used by /proc/mounts

    The kernel escapes space, tab, newline and backslash in mount points
    as \\040, \\011, \\012 and \\134.

    Args:
        raw_mount_point (str): kind of '/media/user/Windows\\040Drive'

    Returns:
        str: kind of '/media/user/Windows Drive'
    """
    return re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), raw_mount_point)


def mounts_to_try():
    mounts = []
    with open(PROC_MOUNTS) as f:
        for line in f:
            if line.find("/dev") == 0 and line.find("/dev/loop") != 0:
                mount_point = decode_mount_point(line.split(" ")[1])
                mounts.append(mount_point)

    return mounts


def locate_windows_mount_points():
    win_mount_points = []
    for mount_point in mounts_to_try():
        # escape glob metacharacters in labels like "Windows [C]"
        result = glob.glob(os.path.join(glob.escape(mount_point), WINDOWS10_REGISTRY_PATH))
        if len(result) == 1:
            win_mount_points.append(mount_point)

    return win_mount_points
