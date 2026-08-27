Sync Bluetooth for dualboot Linux and Windows
=============================================

User-friendly CLI that makes your Bluetooth devices work in both Windows and
Linux without the re-pairing chore. It copies the pairing keys from Linux into
the Windows registry, so you don't have to reboot back and forth.

* doesn't require rebooting multiple times
* discovers the mounted Windows partition automatically
* safe, size-preserving Windows Registry update via `chntpw/reged`
* backs up the Windows Registry before writing
* `--dry-run` to preview any command

## Requirements

* [uv](https://docs.astral.sh/uv/)
* `chntpw` (`sudo apt install chntpw` on Ubuntu/Mint)

## Quick start

Pair your devices on Windows, boot to Linux, pair them there too, then:

```console
# mount the Windows partition read-write, then:
$ sudo uvx --from bt-dualboot-sync bt-dualboot --sync-all
```

List devices and sync a single one:

```console
$ sudo uvx --from bt-dualboot-sync bt-dualboot -l
$ sudo uvx --from bt-dualboot-sync bt-dualboot --sync C2:9E:1D:E2:3D:A5
```

For a persistent command: `uv tool install bt-dualboot-sync`

## Documentation

Full usage, troubleshooting, advanced options and CLI reference:
https://github.com/vhrabar/bt-dualboot

## License

Released under the MIT License. See [`LICENSE`](https://github.com/vhrabar/bt-dualboot/blob/main/LICENSE).

Fork of [x2es/bt-dualboot](https://github.com/x2es/bt-dualboot) by Konstantin Ivanov.

Copyright © 2022 Konstantin Ivanov
Copyright © 2026 Vedran Hrabar
