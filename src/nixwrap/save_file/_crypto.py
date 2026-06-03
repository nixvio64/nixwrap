"""AES encryption/decryption and CRC32 checksum for Rocket League save files.

Ported from RLSaveViewer / RocketRP.
"""

from Crypto.Cipher import AES as _AES

# Constants from RocketRP AES.cs

AES_KEY: bytes = bytes([
    0xD7, 0x8C, 0x32, 0x4A, 0x94, 0x42, 0x94, 0x3C,
    0x6D, 0x65, 0xCE, 0x98, 0x81, 0x85, 0x4C, 0x41,
    0x68, 0x99, 0x22, 0x0C, 0xC7, 0xA1, 0x46, 0x40,
    0x93, 0x9B, 0x96, 0x3C, 0x93, 0x2A, 0x6F, 0xAF,
])

CRC_SEED: int = 0xEFCBF201

OBJHEADER: int = 0xFFFFFFFF

TYPE_TAGS: set[str] = {
    "BoolProperty", "IntProperty", "QWordProperty", "FloatProperty",
    "StrProperty", "NameProperty", "ByteProperty",
    "ObjectProperty", "StructProperty", "ArrayProperty",
}

SPECIAL_STRUCTS: set[str] = {"Vector", "Rotator", "Guid"}

# CRC32 (matching C# Crc32.CalculateCRC)

def _make_crc_table() -> list[int]:
    t: list[int] = []
    for i in range(256):
        c = i << 24
        for _ in range(8):
            c = ((c << 1) ^ 0x04C11DB7) if c & 0x80000000 else (c << 1)
            c &= 0xFFFFFFFF
        t.append(c)
    return t

_CRC_TABLE: list[int] = _make_crc_table()


def crc32(data: bytes, seed: int = CRC_SEED) -> int:
    """Calculate CRC32 matching the C# implementation used by RL save files."""
    crc = ~seed & 0xFFFFFFFF
    for b in data:
        crc = ((crc << 8) ^ _CRC_TABLE[(crc >> 24) ^ b]) & 0xFFFFFFFF
    return ~crc & 0xFFFFFFFF


# AES ECB wrappers

def aes_decrypt(data: bytes) -> bytes:
    """Decrypt save file data with the hardcoded RL AES key (ECB mode)."""
    return _AES.new(AES_KEY, _AES.MODE_ECB).decrypt(data)


def aes_encrypt(data: bytes) -> bytes:
    """Encrypt data with the hardcoded RL AES key.

    Pads to a 16-byte boundary with null bytes, matching C# EncryptData.
    """
    padded_len = (len(data) + 15) & ~15
    padded = data + b'\x00' * (padded_len - len(data))
    return _AES.new(AES_KEY, _AES.MODE_ECB).encrypt(padded)
