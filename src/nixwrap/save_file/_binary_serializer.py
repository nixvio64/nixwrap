"""UE3 binary property-stream serializer.

Converts Python dicts back into RL's tagged-property binary format.

Ported from RLSaveViewer main.py serialize_property_stream / _serialize_* routines.
"""

from __future__ import annotations

import struct


def write_ue3(s: str) -> bytes:
    """Encode a string in UE3 length-prefixed UTF-8 format."""
    encoded = s.encode('utf-8')
    return struct.pack('<i', len(encoded) + 1) + encoded + b'\x00'


def serialize_property_stream(props: dict) -> bytes:
    """Serialize a dict of properties into the UE3 tagged-property binary format."""
    buf = b''

    scalars = {}
    arrays = {}
    for name, val in props.items():
        if isinstance(val, list):
            arrays[name] = val
        else:
            scalars[name] = val

    for name, val in scalars.items():
        buf += write_ue3(name)
        tag, body = _serialize_value(val)
        buf += write_ue3(tag)
        buf += struct.pack('<i', len(body))
        buf += struct.pack('<i', 0)   # vidx
        buf += body

    for name, arr in arrays.items():
        payload = struct.pack('<i', len(arr))
        for elem in arr:
            _, ebody = _serialize_value(elem, is_array_elem=True)
            payload += ebody

        buf += write_ue3(name)
        buf += write_ue3("ArrayProperty")
        buf += struct.pack('<i', len(payload))
        buf += struct.pack('<i', 0)   # vidx
        buf += payload

    buf += write_ue3("None")
    return buf


# Internals

def _serialize_value(val, is_array_elem: bool = False) -> tuple[str, bytes]:
    if isinstance(val, bool):
        return "BoolProperty", b'\x01' if val else b'\x00'
    elif isinstance(val, int):
        if val > 0x7FFFFFFF or val < -0x80000000:
            return "QWordProperty", struct.pack('<Q', val)
        return "IntProperty", struct.pack('<i', val)
    elif isinstance(val, float):
        return "FloatProperty", struct.pack('<f', val)
    elif isinstance(val, str):
        return "StrProperty", write_ue3(val)
    elif isinstance(val, dict):
        return _serialize_struct(val, is_array_elem)
    elif isinstance(val, list):
        return _serialize_array(val)
    return "IntProperty", struct.pack('<i', 0)


def _serialize_struct(d: dict, is_array_elem: bool = False) -> tuple[str, bytes]:
    tn = d.get("__type", "Unknown")
    props = {k: v for k, v in d.items() if k != "__type"}

    body = b''
    if tn in ("Vector", "Rotator"):
        x = props.get("x", props.get("pitch", 0.0))
        y = props.get("y", props.get("yaw", 0.0))
        z = props.get("z", props.get("roll", 0.0))
        body = struct.pack('<fff', x, y, z)
    elif tn == "Guid":
        if isinstance(d, str):
            body = bytes.fromhex(d.replace('-', ''))
        else:
            body = b'\x00' * 16
    elif tn == "Unknown":
        body = serialize_property_stream(props)
        return "StructProperty", body
    elif '.' in tn and is_array_elem:
        from nixwrap.save_file._crypto import OBJHEADER
        body = struct.pack('<I', OBJHEADER) + serialize_property_stream(props)
    else:
        body = serialize_property_stream(props)

    return "StructProperty", write_ue3(tn) + body


def _serialize_array(lst: list) -> tuple[str, bytes]:
    payload = struct.pack('<i', len(lst))
    for elem in lst:
        _, ebody = _serialize_value(elem, is_array_elem=True)
        payload += ebody
    return "ArrayProperty", payload
