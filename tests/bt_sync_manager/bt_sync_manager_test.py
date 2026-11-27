from pytest import fixture, mark
from unittest.mock import patch
from bt_dualboot.bt_sync_manager import BtSyncManager
from bt_dualboot.bluetooth_device import BluetoothDevice

# EXPERIMENTAL:
# import windows_registry_test fixtures
# implies usage of `tests.bt_windows.shared_fixtures` fixtures
#   which implies `tests.windows_registry.shared_fixtures`
#   with it's `windows_registry_test/sample_data/`
from tests.bt_windows.shared_fixtures import *
from tests.bt_linux.shared_fixtures import *


SAMPLE_PUSH_MAC1 = "C2:9E:1D:E2:3D:A5"
SAMPLE_PUSH_MAC2 = "B8:94:A5:FD:F1:0A"

# test currnetlz known bugs
KNOWN_BUG_MACS = {
    MAC_BLE_SYNCED_ZERO_EDIV_RAND,
    MAC_BLE_NO_WIN_PAIR
}


def macs_of(devices):
    """Sorted MACs of given devices, ignoring KNOWN_BUG_MACS"""
    return sorted(device.mac for device in devices if device.mac not in KNOWN_BUG_MACS)


@fixture
def sync_manager(import_devices_extra, windows_registry):
    return BtSyncManager(windows_registry)


@fixture
@patch("bt_dualboot.bt_linux.devices.LINUX_BT_DIR", bt_linux_sample_01_unwrapped())
def just_pushed(sync_manager):
    sync_manager.push([SAMPLE_PUSH_MAC1])
    sync_manager.flush_cache()


@patch("bt_dualboot.bt_linux.devices.LINUX_BT_DIR", bt_linux_sample_01_unwrapped())
class TestBtSyncManager__Initial:
    def test_devices_both_synced(self, sync_manager):
        expected_macs = [
            "A4:BF:C6:D0:E5:FF",
            "B6:C2:D3:E5:F2:0D",
            "A4:80:1D:C5:4F:7E",
            MAC_BLE_SYNCED,
        ]

        devices = sync_manager.devices_both_synced()
        assert macs_of(devices) == sorted(expected_macs)

    def test_devices_needs_sync(self, sync_manager):
        expected_macs = [
            "C2:9E:1D:E2:3D:A5",
            "B8:94:A5:FD:F1:0A",
            MAC_NEED_SYNC_SAME_ADAPTER,
        ]

        devices = sync_manager.devices_needs_sync()
        assert macs_of(devices) == sorted(expected_macs)

    def test_devices_absent_windows(self, sync_manager):
        expected_macs = ["D1:8A:4E:71:5D:C1", "C4:72:B3:6F:82:42"]

        devices = sync_manager.devices_absent_windows()
        assert macs_of(devices) == sorted(expected_macs)

    def test_devices_without_pairingkey(self, sync_manager):
        expected_macs = ["22:94:90:56:EE:38"]

        devices = sync_manager.devices_without_pairingkey()
        assert macs_of(devices) == sorted(expected_macs)


@patch("bt_dualboot.bt_linux.devices.LINUX_BT_DIR", bt_linux_sample_01_unwrapped())
class TestBtSyncManager__AfterSync:
    def test_devices_both_synced(self, sync_manager, just_pushed):
        expected_macs = [
            "A4:BF:C6:D0:E5:FF",
            "B6:C2:D3:E5:F2:0D",
            "A4:80:1D:C5:4F:7E",
            "C2:9E:1D:E2:3D:A5",
            MAC_BLE_SYNCED,
        ]

        devices = sync_manager.devices_both_synced()
        assert macs_of(devices) == sorted(expected_macs)

    def test_devices_needs_sync(self, sync_manager, just_pushed):
        expected_macs = [
            "B8:94:A5:FD:F1:0A",
            MAC_NEED_SYNC_SAME_ADAPTER,
        ]

        devices = sync_manager.devices_needs_sync()
        assert macs_of(devices) == sorted(expected_macs)

    def test_devices_absent_windows(self, sync_manager, just_pushed):
        expected_macs = ["D1:8A:4E:71:5D:C1", "C4:72:B3:6F:82:42"]

        devices = sync_manager.devices_absent_windows()
        assert macs_of(devices) == sorted(expected_macs)


@patch("bt_dualboot.bt_linux.devices.LINUX_BT_DIR", bt_linux_sample_01_unwrapped())
class TestBtSyncManager__push:
    def assert_effect(self, sync_manager):
        expected_macs = ["B8:94:A5:FD:F1:0A", MAC_NEED_SYNC_SAME_ADAPTER]

        devices = sync_manager.devices_needs_sync()
        assert macs_of(devices) == sorted(expected_macs)

    def test_ensure_push_resets_cache(self, sync_manager):
        # populate & corrupt cache
        sync_manager.devices_needs_sync()
        sync_manager.index_cache[SAMPLE_PUSH_MAC1].pop()

        sync_manager.push(BluetoothDevice(mac=SAMPLE_PUSH_MAC1))
        # EXPECT no exceptions raised
        assert True

    def test_push_accept_single_mac(self, sync_manager):
        sync_manager.push(SAMPLE_PUSH_MAC1)
        self.assert_effect(sync_manager)

    def test_push_accept_list_of_macs(self, sync_manager):
        sync_manager.push([SAMPLE_PUSH_MAC1])
        self.assert_effect(sync_manager)

    def test_push_accept_single_bt_instance(self, sync_manager):
        sync_manager.push(BluetoothDevice(mac=SAMPLE_PUSH_MAC1))
        self.assert_effect(sync_manager)

    def test_push_accept_list_of_bt_instances(self, sync_manager):
        sync_manager.push([BluetoothDevice(mac=SAMPLE_PUSH_MAC1)])
        self.assert_effect(sync_manager)

    def test_push_updates_multiple_devices(self, sync_manager):
        sync_manager.push([SAMPLE_PUSH_MAC1, SAMPLE_PUSH_MAC2])
        assert macs_of(sync_manager.devices_needs_sync()) == [MAC_NEED_SYNC_SAME_ADAPTER]


@mark.bug
@patch("bt_dualboot.bt_linux.devices.LINUX_BT_DIR", bt_linux_sample_01_unwrapped())
class TestBtSyncManager__KnownBugs:
    """Regression tests for #25, #26, #27. Run with `-m bug` (dev/start-tests-bug)"""

    def test_push_same_adapter_writes_all_devices(self, sync_manager):
        """#25: classic devices sharing an adapter must all be written"""
        pushed = [MAC_NEED_SYNC_2, MAC_NEED_SYNC_SAME_ADAPTER]
        sync_manager.push(pushed)

        needs_sync_macs = [device.mac for device in sync_manager.devices_needs_sync()]
        assert set(pushed) & set(needs_sync_macs) == set()

    def test_ble_zero_ediv_rand_is_synced(self, sync_manager):
        """#26: EDiv=0 / Rand=0 are valid LE Secure Connections values"""
        both_synced_macs = [device.mac for device in sync_manager.devices_both_synced()]
        needs_sync_macs = [device.mac for device in sync_manager.devices_needs_sync()]

        assert MAC_BLE_SYNCED_ZERO_EDIV_RAND in both_synced_macs
        assert MAC_BLE_SYNCED_ZERO_EDIV_RAND not in needs_sync_macs

    def test_synced_returns_bool(self):
        """#26: synced() must not fall through to None"""
        ltk = "E25A7C3B9D02E25A7C3B9D02E25A7C3B"
        linux = BluetoothDevice(mac=MAC_BLE_SYNCED_ZERO_EDIV_RAND, ltk=ltk, ediv=0, rand=0)
        windows = BluetoothDevice(mac=MAC_BLE_SYNCED_ZERO_EDIV_RAND, ltk=ltk, ediv=0, rand=0)
        no_keys = BluetoothDevice(mac=MAC_BLE_SYNCED_ZERO_EDIV_RAND)

        assert linux.synced(windows) is True
        assert no_keys.synced(windows) is False

    def test_ble_only_device_absent_windows(self, sync_manager):
        """#27: a BLE device with an LTK but no Windows pairing has to be paired in Windows"""
        absent_macs = [device.mac for device in sync_manager.devices_absent_windows()]
        no_key_macs = [device.mac for device in sync_manager.devices_without_pairingkey()]

        assert MAC_BLE_NO_WIN_PAIR in absent_macs
        assert MAC_BLE_NO_WIN_PAIR not in no_key_macs
        # a device with no key of either kind stays under "Missing pairing key"
        assert "22:94:90:56:EE:38" in no_key_macs
