# RPM packaging for bt-dualboot-sync

%global forgeurl https://github.com/vhrabar/bt-dualboot
%global srcname  bt-dualboot

%{!?pkg_version:%global pkg_version 0.1.0}

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
