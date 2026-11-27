from bt_dualboot.bt_linux.bluetooth_device_factory import *
import os

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_samples")
SMPL_BT_SAMPLE_01 = os.path.join(SAMPLES_DIR, "bt_sample_01")
SAMPLE_DEVICE_INFO_PATH = os.path.join(
    SMPL_BT_SAMPLE_01, "A4:6B:6C:9D:E2:FB", "B6:C2:D3:E5:F2:0D", "info"
)
SAMPLE_DEVICE_INFO_PATH_NO_LINKKEY = os.path.join(
    SMPL_BT_SAMPLE_01, "A4:6B:6C:9D:E2:FB", "22:94:90:56:EE:38", "info"
)

SAMPLE_DEVICE_INFO_PATH_BLE = os.path.join(
    SMPL_BT_SAMPLE_01, "A4:6B:6C:9D:E2:FB", "E1:5A:7C:3B:9D:01", "info"
)
SAMPLE_DEVICE_INFO_PATH_BLE_ZERO = os.path.join(
    SMPL_BT_SAMPLE_01, "A4:6B:6C:9D:E2:FB", "E2:5A:7C:3B:9D:02", "info"
)


def test_extract_macs():
    expected = {"device_mac": "B6:C2:D3:E5:F2:0D", "adapter_mac": "A4:6B:6C:9D:E2:FB"}
    assert extract_macs(SAMPLE_DEVICE_INFO_PATH) == expected


def test_extract_info():
    expected = {
        "name": "DEV-1-02-Name",
        "class": "0x000540",
        "pairing_key": "A515CBE4E8F2E236FF999C0A53369EF6",
        "long_term_key": None,
        "ediv": None,
        "rand": None,
    }
    assert extract_info(SAMPLE_DEVICE_INFO_PATH) == expected


def test_extract_info_no_linkkey():
    expected = {
        "name": "DEV-1-02-Name",
        "class": "0x000540",
        "pairing_key": None,
        "long_term_key": None,
        "ediv": None,
        "rand": None,
    }
    assert extract_info(SAMPLE_DEVICE_INFO_PATH_NO_LINKKEY) == expected


def test_bluetooth_device_factory():
    device = bluetooth_device_factory(SAMPLE_DEVICE_INFO_PATH)

    # fmt: off
    assert device.__class__.__name__    == "BluetoothDevice"
    assert device.klass                 == "0x000540"
    assert device.mac                   == "B6:C2:D3:E5:F2:0D"
    assert device.name                  == "DEV-1-02-Name"
    assert device.pairing_key           == "A515CBE4E8F2E236FF999C0A53369EF6"
    # fmt: on

def test_bluetooth_device_factory_no_linkkey():
    device = bluetooth_device_factory(SAMPLE_DEVICE_INFO_PATH_NO_LINKKEY)

    # fmt: off
    assert device.__class__.__name__    == "BluetoothDevice"
    assert device.klass                 == "0x000540"
    assert device.mac                   == "22:94:90:56:EE:38"
    assert device.name                  == "DEV-1-02-Name"
    assert device.pairing_key           == None
    # fmt: on


def test_extract_info_ble():
    expected = {
        "name": "DEV-1-06-Name",
        "class": None,
        "pairing_key": None,
        "long_term_key": "E15A7C3B9D01E15A7C3B9D01E15A7C3B",
        "ediv": "41253",
        "rand": "9862138215374452257",
    }
    assert extract_info(SAMPLE_DEVICE_INFO_PATH_BLE) == expected


def test_bluetooth_device_factory_ble():
    device = bluetooth_device_factory(SAMPLE_DEVICE_INFO_PATH_BLE)

    # fmt: off
    assert device.mac                   == "E1:5A:7C:3B:9D:01"
    assert device.pairing_key           is None
    assert device.ltk                   == "E15A7C3B9D01E15A7C3B9D01E15A7C3B"
    assert device.ediv                  == 41253
    assert device.rand                  == 9862138215374452257
    # fmt: on


def test_bluetooth_device_factory_ble_zero_ediv_rand():
    device = bluetooth_device_factory(SAMPLE_DEVICE_INFO_PATH_BLE_ZERO)

    # fmt: off
    assert device.ltk                   == "E25A7C3B9D02E25A7C3B9D02E25A7C3B"
    assert device.ediv                  == 0
    assert device.rand                  == 0
    # fmt: on
