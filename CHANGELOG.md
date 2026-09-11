# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- The first release of this fork of [x2es/bt-dualboot](https://github.com/x2es/bt-dualboot): it carries the community fixes that were merged upstream but never published, and modernises packaging, tooling and CI around `uv` package manager. 
- Published to PyPI as `bt-dualboot-sync` (the command is still `bt-dualboot`).
- Bluetooth 5.1 / LE device support: LTK, ERand and EDIV keys are read from the Linux `info` file and written to `ControlSet001\Services\BTHPORT\Parameters\Keys` in the Windows registry. Contributed by [@Simon128](https://github.com/Simon128); never released upstream.
- `--list` reports a *Missing pairing key* group for devices that have no key to sync, instead of leaving them unexplained. Contributed by [@asarium](https://github.com/asarium) in [#1](https://github.com/vhrabar/bt-dualboot/pull/1); never released upstream.
- `dev/start-windows-vm`, which boots the installed Windows partition in a QEMU VM with the Bluetooth adapter passed through, so a sync can be verified without rebooting. Autodetects the Windows disk and the Bluetooth USB device, with manual overrides.

### Changed

- Requires Python 3.11 or newer; tested against 3.11, 3.12 and 3.13.
- Packaging moved from Poetry to `uv` with the `hatchling` build backend; `uv.lock` replaces `poetry.lock`.
- Docker images and the `dev/` scripts install and run the project through `uv`.

### Fixed

- No longer crashes on devices without a `LinkKey` in the Windows registry. Contributed by [@asarium](https://github.com/asarium) in [#1](https://github.com/vhrabar/bt-dualboot/pull/1); never released upstream.
- `[General]/Class=` in `/var/lib/bluetooth/ADAPTER_MAC/DEVICE_MAC/info` is treated as optional, instead of failing when it is absent. Fixed upstream by [@x2es](https://github.com/x2es) in [x2es/bt-dualboot#4](https://github.com/x2es/bt-dualboot/pull/4); never released.
- The "paired for multiple BT-adapters" warnings print the device MACs again; they were literal text because of a missing f-string prefix. Fixed upstream by [@J3RN](https://github.com/J3RN) in [x2es/bt-dualboot#9](https://github.com/x2es/bt-dualboot/pull/9); never released.
- `raise ... from err` on the device-not-found path, so the underlying error is no longer reported as an unexpected exception during handling.


[Unreleased]: https://github.com/vhrabar/bt-dualboot/commits/main
