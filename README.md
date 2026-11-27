Sync Bluetooth for dualboot Linux and Windows
=============================================

User-friendly tool that makes your Bluetooth devices work in both Windows and Linux without the re-pairing chore.
  [more about the dualboot Bluetooth issue](#dualboot-bluetooth-issue)

### bt-dualboot
  * doesn't require rebooting 3 times
  * asks you for as few details as possible
  * works with classic and Bluetooth LE devices
  * ... [see all advantages and alternatives](#advantages-and-alternatives)

[How to install](#install)

**For developers**: check out the [Developer insights](README-dev.md) for useful development and testing tips.

### Usage: shortest way

Assuming you already have paired devices in Windows, boot to Linux and pair them there too.
Syncing is then as simple as the following 2 steps:

**1. Mount the Windows partition**

The application probes and uses the mounted Windows partition automatically. Otherwise use [--win /mnt/win/path/](#--win-mntwinpath).
The partition must be mounted with [write access](#troubleshooting-windows-partition-write-access).

**2. Sync all devices available for sync**

```console
$ sudo bt-dualboot --sync-all

Syncing...
==========
 [C2:9E:1D:E2:3D:A5] Keyboard K380
...done

```

NOTES:
  (i) **sudo** tip: this tool needs read-only access to Bluetooth device configuration files, which are inaccessible to a regular user. If you run it through `uvx` rather than a [distribution package](#distribution-packages), see [the uv notes](#with-uv).
  (ii) [--backup vs --no-backup](#--backup-vs---no-backup): you will be asked about your Windows Registry backup strategy
  (iii) use `--dry-run` to preview the effects of any command

### Usage: choose the device manually

1. List device info

```console
$ sudo bt-dualboot -l

Works both in Linux and Windows
===============================
 [A4:BF:C6:D0:E5:FF] WH-1000XM4

Needs sync
==========

Following devices available for sync with `--sync-all` or `--sync MAC` options.

 [C2:9E:1D:E2:3D:A5] Keyboard K380

Have to be paired in Windows
============================

Following devices unavailable for sync unless you boot Windows and pair them

 [E9:1D:FE:2A:C3:C8] JBL GO

Missing pairing key
===================

Following devices do not have a pairing key and so cannot be synced

 [22:94:90:56:EE:38] Mouse M590

```


2. Sync devices using their MAC

```console
$ sudo bt-dualboot --sync C2:9E:1D:E2:3D:A5

Syncing...
==========
 [C2:9E:1D:E2:3D:A5] Keyboard K380
...done

```

See [`bt-dualboot -h`](#cli-reference), `man bt-dualboot` and the chapters below for details.

## Install

### Distribution packages

Native packages pull in `chntpw` and install the `bt-dualboot` command and its man page.

**Ubuntu and derivatives**: [`ppa:vhrabar/tools`](https://launchpad.net/~vhrabar/+archive/ubuntu/tools):

```console
$ sudo add-apt-repository ppa:vhrabar/tools
$ sudo apt install bt-dualboot-sync
```

**Fedora and rpm-based distributions**: [`copr:vhrabar/bt-dualboot-sync`](https://copr.fedorainfracloud.org/coprs/vhrabar/bt-dualboot-sync/):

```console
$ sudo dnf copr enable vhrabar/bt-dualboot-sync
$ sudo dnf install bt-dualboot-sync
```

**Arch and derivatives**: [`bt-dualboot-sync`](https://aur.archlinux.org/packages/bt-dualboot-sync) in the AUR:

```console
$ yay -S bt-dualboot-sync
```

### With uv

On any other distribution (including Ubuntu 24.04), run it from PyPI with [uv](https://docs.astral.sh/uv/). 
This needs Python 3.11+ (uv fetches it on demand) and the `chntpw` package installed separately (see https://pogostick.net/~pnh/ntpasswd/):

```console
$ uvx --from bt-dualboot-sync bt-dualboot --help
```

For a persistent `bt-dualboot` command:

```console
$ uv tool install bt-dualboot-sync
```

NOTES: **sudo** — `--sync*` and `-l` require read-only access to Bluetooth device configuration files, which are inaccessible to a regular user, 
so run those under `sudo`. Make sure `uvx` (or the `uv tool` binary) is reachable by root: install uv system-wide, o
r use `sudo env "PATH=$PATH" uvx --from bt-dualboot-sync bt-dualboot ...`.

### Supported OS

Supported:

* Potentially any Linux-based system that keeps its Bluetooth configuration in `/var/lib/bluetooth` in the same format as BlueZ on Ubuntu
* Windows 10+

Tested on: Windows 10/11 and Ubuntu 25.10/26.04/26.10, Fedora 44/45 and Arch Linux.

## Advanced usage

### --backup vs --no-backup

The Windows Registry update is performed in a safe way using `chntpw/reged` without changing the Hive file's size (`reged -N -E`). Nevertheless, `chntpw` is an unofficial tool, so a backup is not a bad idea. The application performs it however you prefer.

You have to choose your backup strategy explicitly.

```console
$ sudo bt-dualboot --sync-all
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
$ bt-dualboot --list-win-mounts

Windows locations:
==================
 /media/user/win_foo
 /media/user/win_bar

$ sudo bt-dualboot --win /media/user/win_foo -l
```

#### Troubleshooting: Windows partition write access

If the Windows partition is mounted read-only, you have to remount it read-write:

```console
$ sudo mount -o remount,rw /mnt/win/path
```

If it still mounts read-only, Windows was most likely hibernated or shut down with Fast Startup enabled. Disable Fast Startup in Windows and shut it down fully.

### Machine processing

The `--bot` flag enables more parsable output for use in scripts.


## Dualboot Bluetooth issue

Every time a Bluetooth device is paired in one dualboot OS, it stops working in the other. This happens because both OSes use the same Bluetooth adapter with the same MAC. Each pairing process generates new pairing keys for the adapter's MAC, so the previous pairing key saved in the other OS becomes obsolete.

The solution is to sync the saved pairing keys between both OSes. This answer describes how to do it manually: https://unix.stackexchange.com/a/255510/411221

This application implements the approach suggested in this [comment](https://unix.stackexchange.com/questions/255509/bluetooth-pairing-on-dual-boot-of-windows-linux-mint-ubuntu-stop-having-to-p#comment545967_255510), which copies pairing keys directly from Linux to Windows, avoiding multiple reboots. For Bluetooth LE devices the LTK, ERand and EDIV keys are copied as well.


## Advantages and alternatives

**bt-dualboot**:

* doesn't require rebooting multiple times
* [simple install](#install) — native packages for Ubuntu, Fedora and Arch, or straight from PyPI
* provides a single [simple CLI](#cli-reference), doesn't require invoking additional scripts
* discovers the mounted Windows partition automatically
* supports classic (BR/EDR) and Bluetooth LE devices
* safe update of the Windows Registry without changing the file size (rewrite only)
* [backs up the Windows Registry](#--backup-vs---no-backup) before the update
* doesn't require importing/exporting files or handling encoding issues
* allows `--dry-run` before making actual changes


## CLI reference

```console
$ bt-dualboot -h
usage: bt-dualboot [-h] [--version] [-l] [--list-win-mounts] [--bot]
                   [--dry-run] [--win MOUNT] [--sync MAC [MAC ...]]
                   [--sync-all] [-n] [-b [path]]

Sync bluetooth keys from Linux to Windows (v0.1.3)

options:
  -h, --help            show this help message and exit
  --version             print version

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
