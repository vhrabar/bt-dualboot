
Sync Bluetooth for dualboot Linux and Windows
=============================================

User-friendly tool that makes your Bluetooth devices work in both Windows and Linux without the re-pairing chore.
  [more about the dualboot Bluetooth issue](#dualboot-bluetooth-issue)

### bt-dualboot
  * doesn't require rebooting 3 times
  * asks you for as few details as possible
  * ... [see all advantages and alternatives](#advantages-and-alternatives)

[How to install](#prerequisites)

**For developers**: check out the [Developer insights](README-dev.md) for useful development and testing tips.

### Usage: shortest way

Assuming you already have paired devices in Windows, boot to Linux and pair them there too.
Syncing is then as simple as the following 2 steps:

**1. Mount the Windows partition**

The application probes and uses the mounted Windows partition automatically. Otherwise use [--win /mnt/win/path/](#--win-mntwinpath).
The partition must be mounted with [write access](#troubleshooting-windows-partition-write-access).

**2. Sync all devices available for sync**

```console
$ sudo uvx --from bt-dualboot-sync bt-dualboot --sync-all

Syncing...
==========
 [C2:9E:1D:E2:3D:A5] Keyboard K380
...done

```

NOTES:
  (i) **sudo** tip: this tool needs read-only access to Bluetooth device configuration files, which are inaccessible to a regular user. Make sure `uvx` is reachable by root (install uv system-wide, or use `sudo env "PATH=$PATH" uvx ...`).
  (ii) [--backup vs --no-backup](#--backup-vs---no-backup): you will be asked about your Windows Registry backup strategy
  (iii) use `--dry-run` to preview the effects of any command

### Usage: choose the device manually

1. List device info

```console
$ sudo uvx --from bt-dualboot-sync bt-dualboot -l

Works both in Linux and Windows
===============================
 [A4:BF:C6:D0:E5:FF] WH-1000XM4

Needs sync
==========

The following devices are available for sync with the `--sync-all` or `--sync MAC` options.

 [C2:9E:1D:E2:3D:A5] Keyboard K380

Have to be paired in Windows
============================

The following devices are unavailable for sync unless you boot Windows and pair them:

 [E9:1D:FE:2A:C3:C8] JBL GO

```


2. Sync devices using their MAC

```console
$ sudo uvx --from bt-dualboot-sync bt-dualboot --sync C2:9E:1D:E2:3D:A5

Syncing...
==========
 [C2:9E:1D:E2:3D:A5] Keyboard K380
...done

```

See [`bt-dualboot -h`](#cli-reference) and the chapters below for details.

## Prerequisites 

* [uv](https://docs.astral.sh/uv/) installed — it fetches Python and the tool on demand.

* `chntpw` package installed:

```console
Ubuntu $ sudo apt install chntpw
...
```

see https://pogostick.net/~pnh/ntpasswd/


## Install

No install step is needed — run it straight from PyPI with `uvx`:

```console
$ uvx --from bt-dualboot-sync bt-dualboot --help
```

For a persistent `bt-dualboot` command:

```console
$ uv tool install bt-dualboot-sync
```

NOTES: **sudo** — `--sync*` and `-l` require read-only access to Bluetooth device configuration files, which are inaccessible to a regular user, so run those under `sudo` (see the sudo tip above). Native OS packages will be added in a future release.

### Supported OS

Tested with Linux Mint 19.3, 20.3 (Ubuntu 18.04 bionic, 20.04 focal) and Windows 10.

Supported: 

* Potentially any Linux-based system that keeps its Bluetooth configuration in a similar format to Ubuntu
* Windows 10+

More OSes will be tested in future releases, and Mac OS support will be added. If you get a success or failure result for any OS not listed as supported, please share your experience at https://github.com/x2es/bt-dualboot/issues/1.


## Advanced usage

### --backup vs --no-backup

The Windows Registry update is performed in a safe way using `chntpw/reged` without changing the Hive file's size (`reged -N -E`). Nevertheless, `chntpw` is an unofficial tool, so a backup is not a bad idea. The application performs it however you prefer.

You have to choose your backup strategy explicitly.

```console
$ sudo uvx --from bt-dualboot-sync bt-dualboot --sync-all 
usage: ....
bt-dualboot: error: Neither backup option given!

    Windows Registry Hive file will be updated!
    chntpw/reged tool is non-official and hackish Hive file editing tool.
    It is recommended to do backup prior writing into Hive file.

    Use:
      -b [path], --backup [path]    [default: /var/backup/bt-dualboot]
      -n, --no-backup               process without backup

    WARNING:
        Windows Registry Hive file may contain sensitive data. You shouldn't keep this file
        on a storage which may be accessed by others. Consider to remove backup files as soon
        as possible after ensure Windows boots and works correctly.
```

### --win /mnt/win/path/

By default the application recognizes and uses the mounted Windows partition. If it isn't found, or more than one Windows partition exists, you have to provide the mount point with the `--win` parameter.

Use `--list-win-mounts` to list the recognized Windows partitions.

```console
$ uvx --from bt-dualboot-sync bt-dualboot --list-win-mounts

Windows locations:
==================
 /media/user/win_foo
 /media/user/win_bar
 
$ sudo uvx --from bt-dualboot-sync bt-dualboot --win /media/user/win_foo -l
```

#### Troubleshooting: Windows partition write access

If the Windows partition is mounted read-only, you have to remount it read-write:

```console
$ sudo mount -o remount,rw /mnt/win/path
```

### Machine processing

The `--bot` flag enables more parsable output for use in scripts.


## Dualboot Bluetooth issue

Every time a Bluetooth device is paired in one dualboot OS, it stops working in the other. This happens because both OSes use the same Bluetooth adapter with the same MAC. Each pairing process generates new pairing keys for the adapter's MAC, so the previous pairing key saved in the other OS becomes obsolete.

The solution is to sync the saved pairing keys between both OSes. This answer describes how to do it manually: https://unix.stackexchange.com/a/255510/411221

This application implements the approach suggested in this [comment](https://unix.stackexchange.com/questions/255509/bluetooth-pairing-on-dual-boot-of-windows-linux-mint-ubuntu-stop-having-to-p#comment545967_255510), which copies pairing keys directly from Linux to Windows, avoiding multiple reboots.


## Advantages and alternatives

**bt-dualboot**:

* doesn't require rebooting multiple times
* [simple install](#prerequisites)
* provides a single [simple CLI](#cli-reference), doesn't require invoking additional scripts
* discovers the mounted Windows partition automatically
* safe update of the Windows Registry without changing the file size (rewrite only)
* [backs up the Windows Registry](#--backup-vs---no-backup) before the update
* doesn't require importing/exporting files or handling encoding issues
* allows `--dry-run` before making actual changes


## CLI reference

```console
$ uvx --from bt-dualboot-sync bt-dualboot -h
usage: bt-dualboot [-h] [-l] [--list-win-mounts] [--bot] [--dry-run] [--win MOUNT] [--sync MAC [MAC ...]] [--sync-all] [-n] [-b [path]]

Sync bluetooth keys from Linux to Windows.

optional arguments:
  -h, --help            show this help message and exit

List resources:
  -l, --list            [root required] list bluetooth devices
  --list-win-mounts     list mounted Windows locations
  --bot                 parsable output for robots (supported: -l)

Sync keys:
  --dry-run             print actions to do without invocation
  --win MOUNT           Windows mount point (advanced usage)
  --sync MAC [MAC ...]  [root required] sync specified device
  --sync-all            [root required] sync all paired devices

Backup Windows Registry:
  -n, --no-backup       process without backup
  -b [path], --backup [path]
                        path to backup directory, default: /var/backup/bt-dualboot
```

## License

Released under the MIT License. See [`LICENSE`](LICENSE).

Fork of [x2es/bt-dualboot](https://github.com/x2es/bt-dualboot) by Konstantin Ivanov.

Copyright © 2022 Konstantin Ivanov

Copyright © 2026 Vedran Hrabar
