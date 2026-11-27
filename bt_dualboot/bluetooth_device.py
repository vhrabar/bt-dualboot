import struct

from bt_dualboot.bt_windows.convert import (
    hex_string_to_reg_hex_b,
    hex_string_to_reg_value,
    mac_to_reg_key,
)
from bt_dualboot.windows_registry import RegistryError


class BluetoothDevice:
    """Representation of bluetooth device

    Properties:
        klass (str)
        mac (str)
        name (str)
        pairing_key (str)
        ltk (str)
        rand (int)
        ediv (int)
        adapter_mac (str)
        source (str): kind of 'Windows', 'Linux'

    """

    def __init__(
        self,
        mac=None,
        name=None,
        pairing_key=None,
        adapter_mac=None,
        device_class=None,
        source=None,
        ltk=None,
        rand=None,
        ediv=None,
    ):
        # fmt: off
        self.source         = source
        self.klass          = device_class
        self.mac            = mac
        self.name           = name
        self.pairing_key    = pairing_key
        self.adapter_mac    = adapter_mac
        # bluetooth 5.1
        self.ltk            = ltk
        self.rand           = rand
        self.ediv           = ediv
        # fmt: on

    def __repr__(self):
        source = "?"
        if self.source is not None:
            source = self.source[0]
        return f"{self.__class__} {source} [{self.mac}] {self.name}"

    def _get_reg_adapter_section_key(self):
        if self.pairing_key:
            return (
                r"ControlSet001\Services\BTHPORT\Parameters\Keys"
                + "\\"
                + mac_to_reg_key(self.adapter_mac)
            )
        if self.ltk:
            return (
                r"ControlSet001\Services\BTHPORT\Parameters\Keys"
                + "\\"
                + mac_to_reg_key(self.adapter_mac)
                + "\\"
                + mac_to_reg_key(self.mac)
            )
        raise RegistryError(f"Missing pairing key or long term key for {self.adapter_mac}/{self.mac}")

    def rand_to_erand(self):
        # hex(b) type -> 64 bit -> 8 byte in little endian
        hex_string = struct.pack("<Q", self.rand).hex().upper()
        return hex_string_to_reg_hex_b(hex_string)

    def ediv_to_dword(self):
        # .reg dword: text represents the numeric hexadecimal value, not the
        # little-endian byte sequence used to store REG_DWORD in the hive.
        dword_val = struct.pack(">I", self.ediv).hex()
        return f"dword:{dword_val}"

    def for_win_import(self):
        if self.pairing_key:
            device_key = f'"{mac_to_reg_key(self.mac)}"'
            pairing_key = hex_string_to_reg_value(self.pairing_key)
            return self._get_reg_adapter_section_key(), {device_key: pairing_key}
        elif self.ltk:
            return self._get_reg_adapter_section_key(), {
                '"LTK"': hex_string_to_reg_value(self.ltk),
                '"ERand"': self.rand_to_erand(),
                '"EDIV"': self.ediv_to_dword(),
            }
        raise RegistryError(f"Device {self.mac} has neither pairing key, nor long term key")

    def synced(self, other):
        if self.pairing_key:
            return self.pairing_key == other.pairing_key
        # EDiv=0 / Rand=0 are valid: BlueZ stores them for LE Secure Connections
        if self.ltk and self.rand is not None and self.ediv is not None:
            return self.ltk == other.ltk and self.rand == other.rand and self.ediv == other.ediv
        return False

    @classmethod
    def source_linux(cls):
        return "Linux"

    @classmethod
    def source_windows(cls):
        return "Windows"

    def is_source_linux(self):
        return self.source == "Linux"

    def is_source_windows(self):
        return self.source == "Windows"

    def has_pairing_key(self):
        return self.pairing_key is not None

    def has_any_key(self):
        """True when the device has a classic LinkKey or a BLE LongTermKey"""
        return self.pairing_key is not None or self.ltk is not None
