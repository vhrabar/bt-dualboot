from operator import itemgetter

from tests_integration.helpers import snapshot_cli_result


def snapshot_cli(*args, **kwrd):
    context = "[env_no_windows] chntpw installed, no Windows partition mounted"
    return snapshot_cli_result(*args, context=context, **kwrd)


def test_list_win_mounts(snapshot):
    """should exit 0 and say that no Windows partition was found"""
    for res in snapshot_cli(snapshot, ["--list-win-mounts"]):
        retcode, stdout = itemgetter("retcode", "stdout")(res)
        assert stdout.find("No Windows partitions found") > 0
        assert retcode == 0


def test_list(snapshot):
    """-l without --win still needs exactly one Windows location"""
    for res in snapshot_cli(snapshot, ["-l"]):
        retcode, stderr = itemgetter("retcode", "stderr")(res)
        assert stderr.find("Windows locations found, use `--win MOUNT`") > 0
        assert retcode == 1
