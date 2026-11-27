from .shared_fixtures import *
from bt_dualboot.bt_windows.devices import *

#
# NOTE: helper `wp()` imported from `tests.windows_registry.shared_fixtures`
#

"""
@see tests.bt_windows.shared_fixtures for test set explanation
"""


def test_extract_adapter_mac():
    key = r"ControlSet001\Services\BTHPORT\Parameters\Keys\d46d6d97629b"
    assert extract_adapter_mac(key) == "D4:6D:6D:97:62:9B"


def test_get_devices(windows_registry, import_devices, test_scheme):
    devices = get_devices(windows_registry)

    for device in devices:
        assert device.mac in list(test_scheme[device.adapter_mac].keys())
        assert device.pairing_key == test_scheme[device.adapter_mac][device.mac]


def test_get_devices__source(windows_registry, import_devices):
    devices = get_devices(windows_registry)
    for device in devices:
        assert device.is_source_windows()


def test_get_devices__extra(
    windows_registry, import_devices_extra, test_scheme, test_scheme_extra, test_scheme_ble
):
    devices = get_devices(windows_registry)
    classic = {
        (adapter_mac, device_mac): pairing_key
        for scheme in (test_scheme, test_scheme_extra)
        for adapter_mac, adapter_devices in scheme.items()
        for device_mac, pairing_key in adapter_devices.items()
        if device_mac != "MasterIRK"
    }
    ble = {
        (adapter_mac, device_mac): keys
        for adapter_mac, adapter_devices in test_scheme_ble.items()
        for device_mac, keys in adapter_devices.items()
    }

    actual_classic = {(d.adapter_mac, d.mac): d.pairing_key for d in devices if d.pairing_key}
    actual_ble = {
        (d.adapter_mac, d.mac): {"ltk": d.ltk, "ediv": d.ediv, "rand": d.rand} for d in devices if d.ltk
    }

    assert actual_classic == classic
    assert actual_ble == ble
