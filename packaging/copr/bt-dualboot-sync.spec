# RPM packaging for bt-dualboot-sync

%global forgeurl https://github.com/vhrabar/bt-dualboot
%global srcname  bt-dualboot

%{!?pkg_version:%global pkg_version 0.1.4}

Name:           bt-dualboot-sync
Version:        %{pkg_version}
Release:        1%{?dist}
Summary:        Sync Bluetooth pairing keys from Linux to Windows

License:        MIT
URL:            %{forgeurl}
Source0:        %{forgeurl}/archive/v%{version}/%{srcname}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros

# reged(8), which rewrites the Windows registry hive in place
Requires:       chntpw

%description
A Bluetooth device paired under both Linux and Windows stores a different
pairing key in each system, and the device keeps only the most recent one. On a
dualboot machine that means re-pairing the device after every reboot into the
other system.

bt-dualboot copies the pairing keys Linux holds for a device into the Windows
registry hive on a mounted Windows partition, so both systems authenticate with
the same key. It discovers the mounted Windows partition on its own, backs the
hive up before writing, and offers a dry run for every command.

%prep
%autosetup -n %{srcname}-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files -l bt_dualboot

install -Dpm 0644 packaging/bt-dualboot.1 %{buildroot}%{_mandir}/man1/bt-dualboot.1

%check
%pyproject_check_import

%files -f %{pyproject_files}
%doc README.md
%{_bindir}/bt-dualboot
%{_mandir}/man1/bt-dualboot.1*

%changelog
* Fri Nov 27 2026 Vedran Hrabar <vedran.hrabar@outlook.com> - 0.1.4-1
- Changed: Devices are listed in a stable order (sorted by adapter and
  device MAC) by `-l` and `--sync-all`, instead of the order the filesystem
  happens to return them in.
- Changed: `--list-win-mounts` lists every Windows partition it finds and
  exits successfully when there are none or several, which is when it is
  most useful. It prints "No Windows partitions found" instead of an empty
  list. `-l`, `--sync`, `--sync-all` and `--backup` still need exactly one
  Windows partition, or `--win`.
- Changed: Registry errors are reported as a short message instead of a
  Python traceback: what failed, that nothing was changed, and the usual
  causes (a read-only mount, or Windows Fast Startup or hibernation). The
  exit status is 1. `DEBUG=1` still shows the traceback.
- Changed: `--sync` rejects a MAC address that is not in the full
  `XX:XX:XX:XX:XX:XX` form, with a message saying so.
- Changed: The hint for a missing `reged` also gives the `dnf` and `pacman`
  commands for installing `chntpw`.
- Changed: The Ubuntu packages are published for 26.04 and 26.10. 25.10 has
  reached its end of life, and Launchpad no longer accepts uploads for it.
- Fixed: `--sync-all` writes every device. Classic devices paired with the
  same Bluetooth adapter share one registry key, and each one overwrote the
  previous, so only the last device per adapter was saved, while the output
  still said `done`.
- Fixed: BLE devices paired with LE Secure Connections now count as synced
  once pushed. BlueZ stores `EDiv=0` and `Rand=0` for them, which were read
  as missing, so these devices stayed under "Needs sync" and were rewritten
  on every run.
- Fixed: BLE devices with a long-term key that are not paired in Windows are
  listed under "Have to be paired in Windows" instead of "Missing pairing
  key".
- Fixed: A device name containing `%` (such as `JBL 100% Bass`) no longer
  crashes the tool, and neither does a device without a `Name`: it is shown
  by its alias, or by its MAC address when it has no alias either.
- Fixed: Windows partitions mounted at a path with a space, such as the
  common `/media/user/Windows Drive`, or with characters like `[ ]`, are
  found by auto-discovery and `--list-win-mounts`.
- Fixed: A write to a read-only Windows partition is reported as an error.
  `reged` reports success in that case while saving nothing, so the tool
  claimed devices were synced when they were not.
- Fixed: `--sync --dry-run` no longer prints `synced … successfully`.
- Fixed: The Ubuntu packages reach the PPA. Launchpad rejected every 0.1.x
  upload because only the first series' upload carried the source tarball,
  and that series was no longer accepting uploads.
- Fixed: The man page shows the release version. Packages built from the
  release tarball (Ubuntu and Arch) showed 0.1.0.

* Sat Sep 12 2026 Vedran Hrabar <vedran.hrabar@outlook.com> - 0.1.3-1
- Fixed: The Ubuntu packages build again. Releases cut on the same day were
  given changelog timestamps in the wrong order, because the offset that
  separates them was written as `+N minutes`, which GNU date on Ubuntu 24.04
  reads as a timezone rather than a relative time. The timestamps are now
  computed from the epoch, which every supported version reads the same way.

* Sat Sep 12 2026 Vedran Hrabar <vedran.hrabar@outlook.com> - 0.1.2-1
- Fixed: The Ubuntu packages build again: the `Programming Language ::
  Python :: 3.15` classifier was rejected by 25.10, whose
  `trove-classifiers` predates that version, so it is dropped until 3.15 is
  released.
- Fixed: Successive releases cut on the same day no longer share a timestamp
  in the generated `debian/changelog`, which dpkg requires to be strictly
  ordered.

* Sat Sep 12 2026 Vedran Hrabar <vedran.hrabar@outlook.com> - 0.1.1-1
- Added: Distribution packages, built from the release tarball so every
  channel ships the same code as PyPI:
- Added: Ubuntu, from
  [`ppa:vhrabar/tools`](https://launchpad.net/~vhrabar/+archive/ubuntu/tools)
  for 25.10, 26.04 and 26.10.
- Added: Fedora, from
  [`copr:vhrabar/bt-dualboot-sync`](https://copr.fedorainfracloud.org/coprs/vhrabar/bt-dualboot-sync/)
  for 43, 44, 45 and rawhide.
- Added: Arch, as
  [`bt-dualboot-sync`](https://aur.archlinux.org/packages/bt-dualboot-sync)
  in the AUR. It provides and conflicts with `bt-dualboot` and
  `bt-dualboot-ng`, which install the same command.
- Added: A `bt-dualboot(1)` man page, shipped by all three distribution
  packages.

* Sat Sep 12 2026 Vedran Hrabar <vedran.hrabar@outlook.com> - 0.1.0-1
- Added: The first release of this fork of
  [x2es/bt-dualboot](https://github.com/x2es/bt-dualboot): it carries the
  community fixes that were merged upstream but never published, and
  modernises packaging, tooling and CI around `uv` package manager.
- Added: Published to PyPI as `bt-dualboot-sync` (the command is still
  `bt-dualboot`).
- Added: Bluetooth 5.1 / LE device support: LTK, ERand and EDIV keys are
  read from the Linux `info` file and written to
  `ControlSet001\Services\BTHPORT\Parameters\Keys` in the Windows registry.
  Contributed by [@Simon128](https://github.com/Simon128); never released
  upstream.
- Added: `--list` reports a *Missing pairing key* group for devices that
  have no key to sync, instead of leaving them unexplained. Contributed by
  [@asarium](https://github.com/asarium) in
  [#1](https://github.com/vhrabar/bt-dualboot/pull/1); never released
  upstream.
- Added: `dev/start-windows-vm`, which boots the installed Windows partition
  in a QEMU VM with the Bluetooth adapter passed through, so a sync can be
  verified without rebooting. Autodetects the Windows disk and the Bluetooth
  USB device, with manual overrides.
- Changed: Requires Python 3.11 or newer; tested against 3.11, 3.12 and
  3.13.
- Changed: Packaging moved from Poetry to `uv` with the `hatchling` build
  backend; `uv.lock` replaces `poetry.lock`.
- Changed: Docker images and the `dev/` scripts install and run the project
  through `uv`.
- Fixed: No longer crashes on devices without a `LinkKey` in the Windows
  registry. Contributed by [@asarium](https://github.com/asarium) in
  [#1](https://github.com/vhrabar/bt-dualboot/pull/1); never released
  upstream.
- Fixed: `[General]/Class=` in
  `/var/lib/bluetooth/ADAPTER_MAC/DEVICE_MAC/info` is treated as optional,
  instead of failing when it is absent. Fixed upstream by
  [@x2es](https://github.com/x2es) in
  [x2es/bt-dualboot#4](https://github.com/x2es/bt-dualboot/pull/4); never
  released.
- Fixed: The "paired for multiple BT-adapters" warnings print the device
  MACs again; they were literal text because of a missing f-string prefix.
  Fixed upstream by [@J3RN](https://github.com/J3RN) in
  [x2es/bt-dualboot#9](https://github.com/x2es/bt-dualboot/pull/9); never
  released.
- Fixed: `raise ... from err` on the device-not-found path, so the
  underlying error is no longer reported as an unexpected exception during
  handling.
