"""Rocket League .save file I/O.

Decrypts, parses, and (optionally) re-encrypts SaveData files.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path
from typing import Any

from nixwrap.save_file._crypto import (
    AES_KEY, CRC_SEED, OBJHEADER,
    crc32, aes_decrypt, aes_encrypt,
)
from nixwrap.save_file._binary_parser import read_ue3, parse_property_stream
from nixwrap.save_file._binary_serializer import write_ue3, serialize_property_stream


# Decrypt & Parse

def parse_savedata(filepath: str | Path,
                   check_crc: bool = True) -> dict[str, Any]:
    """Decrypt and parse a Rocket League .save file.

    Returns a raw dict with keys:
        file_info, header, object_types, properties, objects
    """
    with open(filepath, 'rb') as f:
        raw = f.read()

    off = 0
    part1_len = struct.unpack_from('<I', raw, off)[0]; off += 4
    part1_crc = struct.unpack_from('<I', raw, off)[0]; off += 4
    encrypted = raw[off:off + part1_len]
    crc_actual = crc32(encrypted)
    crc_ok = part1_crc == crc_actual

    if check_crc and not crc_ok:
        print(
            f"CRC mismatch: expected 0x{part1_crc:08X}, "
            f"got 0x{crc_actual:08X}",
            file=sys.stderr,
        )

    dec = aes_decrypt(encrypted)
    off = 0
    foosball = struct.unpack_from('<I', dec, off)[0]; off += 4
    magic    = struct.unpack_from('<I', dec, off)[0]; off += 4
    eng  = struct.unpack_from('<i', dec, off)[0]; off += 4
    lic  = struct.unpack_from('<i', dec, off)[0]; off += 4
    typv = struct.unpack_from('<i', dec, off)[0]; off += 4
    svlen = struct.unpack_from('<i', dec, off)[0]; off += 4
    svdata = dec[off:off + svlen - 4]; off += svlen - 4

    ntypes = struct.unpack_from('<i', dec, off)[0]; off += 4
    objtypes = []
    for _ in range(ntypes):
        tn, off = read_ue3(dec, off)
        fp = struct.unpack_from('<I', dec, off)[0]; off += 4
        oi = struct.unpack_from('<I', dec, off)[0]; off += 4
        objtypes.append({
            "type": tn,
            "object_index": oi,
            "file_position": fp,
        })

    # Root property stream (skip OBJHEADER at start of savedata)
    sdpos = 4
    props, _ = parse_property_stream(svdata, sdpos)

    objects = []
    for i, ot in enumerate(objtypes):
        obj_pos = ot["file_position"] - 4
        if obj_pos >= len(svdata):
            objects.append({
                "__type": ot["type"],
                "__error": "out of range",
            })
            continue
        end = (
            objtypes[i + 1]["file_position"] - 4
            if i + 1 < len(objtypes)
            else len(svdata)
        )
        obj_bytes = svdata[obj_pos + 4:end]  # skip per-object OBJHEADER
        try:
            oprop, _ = parse_property_stream(obj_bytes, 0)
            oprop["__type"] = ot["type"]
            objects.append(oprop)
        except Exception as e:
            objects.append({
                "__type": ot["type"],
                "__parse_error": str(e),
                "__raw_hex": obj_bytes.hex(),
            })

    return {
        "file_info": {
            "source_file": Path(filepath).name,
            "encrypted_size": part1_len,
            "crc_expected": f"0x{part1_crc:08X}",
            "crc_calculated": f"0x{crc_actual:08X}",
            "crc_match": crc_ok,
        },
        "header": {
            "foosball": f"0x{foosball:08X}",
            "magic": f"0x{magic:08X}",
            "version_info": {
                "engine_version": eng,
                "licensee_version": lic,
                "type_version": typv,
            },
        },
        "object_types": objtypes,
        "properties": props,
        "objects": objects,
    }


# Re-encrypt (EXPERIMENTAL)

def assemble_savedata(data: dict[str, Any], output_path: str | Path) -> None:
    """Serialize a parsed save-data dict back into a .save file.

    EXPERIMENTAL. Round-tripped files may differ in size from the
    original. It is not guaranteed that the game will accept the
    re-encrypted file.
    """
    hdr = data["header"]
    vi = hdr["version_info"]
    ot = data["object_types"]
    props = data["properties"]
    objects = data["objects"]

    prop_bytes = serialize_property_stream(props)
    prop_len = len(prop_bytes) + 4   # + OBJHEADER

    obj_blobs = []
    for obj in objects:
        oprops = {k: v for k, v in obj.items() if k != "__type"}
        obj_blobs.append(serialize_property_stream(oprops))

    sd = struct.pack('<I', OBJHEADER) + prop_bytes
    if obj_blobs:
        new_ot: list[dict[str, Any]] = []
        pos = prop_len
        for i, blob in enumerate(obj_blobs):
            fp = pos
            pos += 4 + len(blob)
            new_ot.append({
                "type": ot[i]["type"],
                "object_index": ot[i]["object_index"],
                "file_position": fp + 4,
            })
            sd += struct.pack('<I', OBJHEADER) + blob
        ot = new_ot

    savedata_len = len(sd) + 4

    buf  = struct.pack('<I', 0xF005BA11)
    buf += struct.pack('<I', 0x7FFFFFFF)
    buf += struct.pack('<iii', vi["engine_version"],
                       vi["licensee_version"], vi["type_version"])
    buf += struct.pack('<i', savedata_len)
    buf += sd
    buf += struct.pack('<i', len(ot))
    for o in ot:
        buf += write_ue3(o["type"])
        buf += struct.pack('<I', o["file_position"])
        buf += struct.pack('<I', o["object_index"])

    encrypted = aes_encrypt(buf)
    crc = crc32(encrypted)
    out  = struct.pack('<I', len(encrypted))
    out += struct.pack('<I', crc)
    out += encrypted

    with open(output_path, 'wb') as f:
        f.write(out)


# Convenience

def save_to_json(data: dict[str, Any], output_path: str | Path,
                 compact: bool = False) -> None:
    """Write parsed save data to a JSON file."""
    indent = None if compact else 2
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
