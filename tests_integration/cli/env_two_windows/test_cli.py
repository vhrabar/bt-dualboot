from operator import itemgetter

from tests_integration.helpers import snapshot_cli_result

WINDOWS_DRIVE = "/media/user/Windows Drive"
WINDOWS_11 = "/mnt/windows11"


def snapshot_cli(*args, **kwrd):
    context = "[env_two_windows] chntpw installed, two Windows partitions mounted"
    return snapshot_cli_result(*args, context=context, **kwrd)


def test_list_win_mounts(snapshot):
    """#28, #29: should list both partitions, including the mount point with a space"""
    for res in snapshot_cli(snapshot, ["--list-win-mounts"]):
        retcode, stdout = itemgetter("retcode", "stdout")(res)
        assert f" {WINDOWS_DRIVE}\n" in stdout
        assert f" {WINDOWS_11}\n" in stdout
        assert retcode == 0


def test_list(snapshot):
    """#28: -l without --win errors when the Windows location is ambiguous"""
    for res in snapshot_cli(snapshot, ["-l"]):
        retcode, stderr = itemgetter("retcode", "stderr")(res)
        assert stderr.find("2 Windows locations found, use `--win MOUNT`") > 0
        assert retcode == 1
