from pytest import fixture

#
# EPERIMENTAL:
#   this module
#       * includes fixtures from foreign module
#       * shares fixtures for other foreign modules
#
from tests.windows_registry.shared_fixtures import *

from bt_dualboot.bt_windows.convert import *

"""
Initializes and chekcs following test set.

    2 BT adapters:
        A (A4:6B:6C:9D:E2:FB):
            4 BT devices,
                2 synced     with Windows               (pairing_keys the same)
                    A4:BF:C6:D0:E5:FF
                    B6:C2:D3:E5:F2:0D

                1 not synced with Windows               (pairing_keys differ)
                    C2:9E:1D:E2:3D:A5

                1 not paired in Windows                 (abset in Windows registry)
                    D1:8A:4E:71:5D:C1

                1 paired in Windows but not in Linux    (eixst in Windows registry)
                    E9:1D:FE:2A:C3:C8

        B (B4:6B:6C:9D:E2:FB):
            3 BT devices
                1 synced     with Windows
                    A4:80:1D:C5:4F:7E

                1 not synced with Windows
                    B8:94:A5:FD:F1:0A

                1 not paired in Windows
                    C4:72:B3:6F:82:42

    Extra set, imported by `import_devices_extra` only (unit tests).
    The integration env imports just `test_scheme`: its --sync-all assertions
    would fail on these devices until #25, #26 and #27 are fixed.

        A (A4:6B:6C:9D:E2:FB):
            1 classic, not synced with Windows, SAME adapter as C2:9E:1D:E2:3D:A5 (#25)
                C5:9E:1D:E2:3D:A6

            1 BLE synced with Windows, non-zero EDiv/Rand
                E1:5A:7C:3B:9D:01

            1 BLE synced with Windows, EDiv=0 / Rand=0 (LE Secure Connections, #26)
                E2:5A:7C:3B:9D:02

            1 BLE not paired in Windows (#27)
                E3:5A:7C:3B:9D:03
"""

# same adapter as MAC_NEED_SYNC_2
MAC_NEED_SYNC_SAME_ADAPTER = "C5:9E:1D:E2:3D:A6"
MAC_BLE_SYNCED = "E1:5A:7C:3B:9D:01"
MAC_BLE_SYNCED_ZERO_EDIV_RAND = "E2:5A:7C:3B:9D:02"
MAC_BLE_NO_WIN_PAIR = "E3:5A:7C:3B:9D:03"

# valid for --sync*
MAC_NEED_SYNC_1 = "B8:94:A5:FD:F1:0A"
MAC_NEED_SYNC_2 = "C2:9E:1D:E2:3D:A5"

# not valid for --sync*
MAC_NO_WIN_PAIR_2 = "D1:8A:4E:71:5D:C1"
UNKNOWN_MAC_1 = "F2:9E:1D:E2:3D:A5"
UNKNOWN_MAC_2 = "E8:94:A5:FD:F1:0A"


@fixture
def test_scheme():
    # fmt: off
    return {
        # adapter MAC
        "A4:6B:6C:9D:E2:FB": {
            # device MAC:        pairing_key                            NOTE
            # -----------        -----------                            ----
            "A4:BF:C6:D0:E5:FF": "A43C6BD9E1592C1FFA0DE17F3DB6F38B",  # same
            "B6:C2:D3:E5:F2:0D": "A515CBE4E8F2E236FF999C0A53369EF6",  # same
            "MasterIRK":         "35353535353535353535353535353535",  # non-MAC value
            "C2:9E:1D:E2:3D:A5": "12121212121212121212121212121212",  # differ
            # absent 'D1:8A:4E:71:5D:C1'
            "E9:1D:FE:2A:C3:C8": "34343434343434343434343434343434",  # not paired in linux
        },
        "B4:6B:6C:9D:E2:FB": {
            "A4:80:1D:C5:4F:7E": "A12B5D441EC1A9D517794FC2B4889202",  # same
            "B8:94:A5:FD:F1:0A": "71717171717171717171717171717171",  # differ
            # absent 'C4:72:B3:6F:82:42'
        },
    }
    # fmt: on


@fixture
def test_scheme_extra():
    # fmt: off
    return {
        "A4:6B:6C:9D:E2:FB": {
            "C5:9E:1D:E2:3D:A6": "56565656565656565656565656565656",  # differ
        },
    }
    # fmt: on


@fixture
def test_scheme_ble():
    # fmt: off
    return {
        # adapter MAC
        "A4:6B:6C:9D:E2:FB": {
            # device MAC         LE keys as stored in Linux `info`                                   NOTE
            "E1:5A:7C:3B:9D:01": {"ltk": "E15A7C3B9D01E15A7C3B9D01E15A7C3B", "ediv": 41253, "rand": 9862138215374452257},  # same
            "E2:5A:7C:3B:9D:02": {"ltk": "E25A7C3B9D02E25A7C3B9D02E25A7C3B", "ediv": 0,     "rand": 0},                    # same
            # absent 'E3:5A:7C:3B:9D:03'
        },
    }
    # fmt: on


def ble_device_reg_values(ble_keys):
    """Windows registry values of a BLE device subkey, encoded independently of BluetoothDevice

    Args:
        ble_keys (dict): kind of {"ltk": "A61B...", "ediv": 41253, "rand": 9862138215374452257}

    Returns:
        dict: kind of {'"LTK"': 'hex:a6,1b,...', '"ERand"': 'hex(b):...', '"EDIV"': 'dword:0000a125'}
    """
    erand_bytes = ble_keys["rand"].to_bytes(8, "little").hex()
    return {
        '"LTK"': hex_string_to_reg_value(ble_keys["ltk"]),
        '"ERand"': hex_string_to_reg_hex_b(erand_bytes),
        '"EDIV"': f"dword:{ble_keys['ediv']:08x}",
    }


@fixture
def import_devices_extra(windows_registry, import_devices, test_scheme_extra, test_scheme_ble):
    """Imports `test_scheme_extra` and `test_scheme_ble` on top of `import_devices`"""
    import_scheme(windows_registry, test_scheme_extra, test_scheme_ble)


@fixture
def import_devices(windows_registry, test_scheme):
    import_scheme(windows_registry, test_scheme)


def import_scheme(windows_registry, scheme, scheme_ble=None):
    """Imports classic pairing keys and BLE device subkeys into the registry

    Args:
        windows_registry (WindowsRegistry)
        scheme (dict): adapter MAC => {device MAC => pairing key}
        scheme_ble (dict): adapter MAC => {device MAC => {ltk, ediv, rand}}
    """
    for_import = {}

    for adapter_mac, devices in scheme.items():
        # SAMPLE: PREFIX\ControlSet001\Services\BTHPORT\Parameters\Keys\d46d6d97629b
        reg_section = wp(
            r"ControlSet001\Services\BTHPORT\Parameters\Keys" + "\\" + mac_to_reg_key(adapter_mac)
        )
        for_import[reg_section] = {}

        for device_mac, pairing_key in devices.items():
            if device_mac != "MasterIRK":
                device_reg_key = mac_to_reg_key(device_mac)
            else:
                device_reg_key = device_mac

            for_import[reg_section][f'"{device_reg_key}"'] = hex_string_to_reg_value(pairing_key)

    for adapter_mac, devices in (scheme_ble or {}).items():
        # SAMPLE: PREFIX\ControlSet001\Services\BTHPORT\Parameters\Keys\d46d6d97629b\e15a7c3b9d01
        for device_mac, ble_keys in devices.items():
            reg_section = wp(
                r"ControlSet001\Services\BTHPORT\Parameters\Keys"
                + "\\"
                + mac_to_reg_key(adapter_mac)
                + "\\"
                + mac_to_reg_key(device_mac)
            )
            for_import[reg_section] = ble_device_reg_values(ble_keys)

    windows_registry.import_dict(for_import, safe=False)
