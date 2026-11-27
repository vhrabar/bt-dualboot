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

SAMPLE_DEVICE_INFO_PATH_PERCENT = os.path.join(
    SMPL_BT_SAMPLE_01, "B4:6B:6C:9D:E2:FB", "C6:25:25:4A:42:4C", "info"
)
SAMPLE_DEVICE_INFO_PATH_NO_NAME = os.path.join(
    SMPL_BT_SAMPLE_01, "B4:6B:6C:9D:E2:FB", "C7:4E:4F:4E:41:4D", "info"
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


def test_extract_info_name_with_percent():
    """#30: `%` in a name is literal, not ConfigParser interpolation"""
    assert extract_info(SAMPLE_DEVICE_INFO_PATH_PERCENT)["name"] == "JBL 100% Bass"


def test_extract_info_no_name_falls_back_to_alias():
    """#30: missing [General] Name falls back to Alias"""
    assert extract_info(SAMPLE_DEVICE_INFO_PATH_NO_NAME)["name"] == "DEV-2-05-Alias"


def test_extract_info_no_name_no_alias_falls_back_to_mac(tmp_path):
    """#30: missing Name and Alias falls back to the device MAC"""
    info_path = tmp_path / "A4:6B:6C:9D:E2:FB" / "C8:00:00:00:00:01" / "info"
    info_path.parent.mkdir(parents=True)
    info_path.write_text("[General]\nTrusted=true\n\n[LinkKey]\nKey=C8000000000001C8000000000001C800\n")

    assert extract_info(str(info_path))["name"] == "C8:00:00:00:00:01"
