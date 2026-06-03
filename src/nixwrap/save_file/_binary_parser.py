"""UE3 binary property-stream parser.

Reads Rocket League's tagged-property binary format into Python dicts.

Ported from RLSaveViewer main.py parse_property_stream / _parse_* routines.
"""

from __future__ import annotations

import struct

from nixwrap.save_file._crypto import TYPE_TAGS, SPECIAL_STRUCTS, OBJHEADER


# String I/O

def read_ue3(data: bytes, offset: int) -> tuple[str, int]:
    """Read a UE3-style length-prefixed string.

    Positive length = UTF-8 (length includes null terminator).
    Negative length = UTF-16-LE (each character = 2 bytes).
    """
    length = struct.unpack_from('<i', data, offset)[0]
    offset += 4
    if length == 0:
        return "", offset
    if length < 0:
        byte_count = (-length) * 2
        raw = data[offset:offset + byte_count]
        if len(raw) >= 2 and raw[-2:] == b'\x00\x00':
            raw = raw[:-2]
        return raw.decode('utf-16-le'), offset + byte_count
    if length > 0:
        s = data[offset:offset + length - 1].decode('utf-8')
        return s, offset + length
    return "", offset


# Property stream

def parse_property_stream(data: bytes, offset: int) -> tuple[dict, int]:
    """Read tagged props until the None sentinel.

    Handles fixed-size arrays via a vidx (value index) mechanism:
    when the same prop name appears multiple times they get collected
    into a list keyed by vidx.
    """
    props: dict = {}
    fixed: dict[str, dict[int, object]] = {}

    while True:
        name, offset = read_ue3(data, offset)
        if name == "None":
            break

        tag_offset = offset
        tag, offset = read_ue3(data, offset)

        if tag not in TYPE_TAGS:
            # no type tag so recurse: either a value-type struct or class-in-array
            offset = tag_offset
            inner, offset = parse_property_stream(data, offset)
            inner["__type"] = name
            val = inner
            vidx = 0
        else:
            vlen = struct.unpack_from('<i', data, offset)[0]; offset += 4
            vidx = struct.unpack_from('<i', data, offset)[0]; offset += 4
            val, offset = _parse_value(data, offset, tag, vlen)

        if vidx != 0:
            fixed.setdefault(name, {})[vidx] = val
        elif name in props or name in fixed:
            fixed.setdefault(name, {})[vidx] = val
        else:
            props[name] = val

    for name, idxmap in fixed.items():
        if name in props:
            idxmap[0] = props.pop(name)
        props[name] = [idxmap[i] for i in sorted(idxmap)]

    return props, offset


# Value parsers

def _parse_value(data: bytes, offset: int, tag: str,
                 vlen: int = 0) -> tuple[object, int]:
    """Dispatch on UE3 type tag."""
    if tag == "BoolProperty":
        return bool(data[offset]), offset + 1
    elif tag == "IntProperty":
        return struct.unpack_from('<i', data, offset)[0], offset + 4
    elif tag == "QWordProperty":
        return struct.unpack_from('<Q', data, offset)[0], offset + 8
    elif tag == "FloatProperty":
        return round(struct.unpack_from('<f', data, offset)[0], 6), offset + 4
    elif tag in ("StrProperty", "NameProperty"):
        return read_ue3(data, offset)
    elif tag == "ByteProperty":
        tn, offset = read_ue3(data, offset)
        if tn == "None":
            return data[offset], offset + 1
        val, offset = read_ue3(data, offset)
        return val, offset
    elif tag == "ObjectProperty":
        return struct.unpack_from('<i', data, offset)[0], offset + 4
    elif tag == "StructProperty":
        return _parse_struct(data, offset)
    elif tag == "ArrayProperty":
        return _parse_array(data, offset, vlen)
    raise ValueError(f"Unknown tag {tag!r} at offset {offset}")


def _parse_struct(data: bytes, offset: int) -> tuple[dict | str, int]:
    """Parse a StructProperty body."""
    tn, offset = read_ue3(data, offset)

    # ISpecialSerialized: fixed binary layout
    if tn == "Vector":
        x, y, z = struct.unpack_from('<fff', data, offset)
        return {"x": round(x, 6), "y": round(y, 6), "z": round(z, 6)}, offset + 12
    if tn == "Rotator":
        p, y, r = struct.unpack_from('<fff', data, offset)
        return {"pitch": round(p, 6), "yaw": round(y, 6), "roll": round(r, 6)}, offset + 12
    if tn == "Guid":
        a, b, c, d = struct.unpack_from('<IIII', data, offset)
        return f"{a:08X}-{b:08X}-{c:08X}-{d:08X}", offset + 16

    # Class in an array: TypeName + 0xFFFFFFFF marker + property stream
    marker = struct.unpack_from('<I', data, offset)[0]
    if marker == OBJHEADER:
        props, offset = parse_property_stream(data, offset + 4)
        props["__type"] = tn
        return props, offset

    # Value-type struct: property stream follows immediately after type name
    props, offset = parse_property_stream(data, offset)
    props["__type"] = tn
    return props, offset


def _parse_array(data: bytes, offset: int, vlen: int) -> tuple[list, int]:
    """Parse an ArrayProperty body."""
    count = struct.unpack_from('<i', data, offset)[0]
    offset += 4
    if count <= 0:
        return [], offset

    # Heuristic: uniform arrays have a known per-element size
    payload = vlen - 4
    elem_hint = payload // count if payload > 0 else 0
    elems: list = []

    if elem_hint == 4:          # int32 array
        for _ in range(count):
            elems.append(struct.unpack_from('<i', data, offset)[0])
            offset += 4
        return elems, offset
    if elem_hint == 1:          # bool array
        for _ in range(count):
            elems.append(data[offset])
            offset += 1
        return elems, offset
    if elem_hint == 8:          # uint64 array
        for _ in range(count):
            elems.append(struct.unpack_from('<Q', data, offset)[0])
            offset += 8
        return elems, offset

    # Fallback: sniff each element
    for _ in range(count):
        elem, offset = _parse_array_elem(data, offset)
        elems.append(elem)
    return elems, offset


def _parse_array_elem(data: bytes, offset: int) -> tuple[object, int]:
    """Sniff the type of a single array element (no type tags in arrays)."""
    try:
        s, after1 = read_ue3(data, offset)
    except (UnicodeDecodeError, struct.error):
        return struct.unpack_from('<i', data, offset)[0], offset + 4

    if s == "None":
        try:
            read_ue3(data, after1)
            return {}, after1          # empty struct
        except Exception:
            return data[after1], after1 + 1  # byte

    if not s:
        return s, after1

    # Class element: TypeName + 0xFFFFFFFF + propstream
    if after1 + 4 <= len(data) and \
       struct.unpack_from('<I', data, after1)[0] == OBJHEADER:
        props, off = parse_property_stream(data, after1 + 4)
        props["__type"] = s
        return props, off

    # Sniff: is the next token a property name or a type tag?
    try:
        maybe_prop, after2 = read_ue3(data, after1)

        if maybe_prop == "StructProperty":
            content = after2 + 8
            if content + 4 <= len(data) and \
               struct.unpack_from('<I', data, content)[0] == OBJHEADER:
                content += 4
            props, off = parse_property_stream(data, content)
            props["__type"] = s
            return props, off

        if maybe_prop in TYPE_TAGS:
            props, off = parse_property_stream(data, offset)
            return props, off

        maybe_tag, _ = read_ue3(data, after2)
        if '.' in s and maybe_tag in TYPE_TAGS:
            props, off = parse_property_stream(data, after1)
            props["__type"] = s
            return props, off
    except Exception:
        pass

    return s, after1
