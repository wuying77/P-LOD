
def decode_frame(data: bytes) -> DecodedFrame:
    if len(data) < 12:
        raise ProtocolError("frame too short")
    if len(data) > MAX_FRAME_SIZE:
        raise ProtocolError("MAX_FRAME_SIZE exceeded")

    magic, ver, flags, count, seq = struct.unpack_from("<HBBHH", data, 0)
    if magic != MAGIC:
        raise ProtocolError(f"bad MAGIC {magic:#x}")
    if ver not in (VERSION_V10, VERSION_V11):
        raise ProtocolError(f"unknown VERSION {ver:#x}")
    if flags & ~KNOWN_FLAGS:
        raise ProtocolError(f"unknown header flags 0x{flags:02X}")
    if count > MAX_SE_NODES:
        raise ProtocolError("SE_NODE_COUNT exceeds MAX_SE_NODES")

    embodied = bool(flags & FLAG_IS_EMBODIED_PROFILE)
    has_meta = bool(flags & FLAG_HAS_EXTENDED_META)
    has_ct = bool(flags & FLAG_HAS_CONSTRAINT_TABLE)
    if ver == VERSION_V10 and (has_meta or has_ct):
        raise ProtocolError("v1.0 frame must not set Extended Meta or Constraint Table flags")

    base = EMBODIED_SIZE if embodied else CORE_SIZE
    off = 8
    nodes: List[SENode] = []
    for _ in range(count):
        need = base + (META_SIZE if has_meta else 0)
        if off + need > len(data) - 4:
            raise ProtocolError("truncated node table")
        if embodied:
            nid, risk, sub, px, py, pz, vx, vy, vz, phase = struct.unpack_from(
                "<HBB3f3ff", data, off
            )
            off += EMBODIED_SIZE
            for v, name in (
                (px, "pos.x"),
                (py, "pos.y"),
                (pz, "pos.z"),
                (vx, "vel.x"),
                (vy, "vel.y"),
                (vz, "vel.z"),
                (phase, "phase"),
            ):
                _check_finite(v, name)
            if nid == GLOBAL_NA:
                raise ProtocolError("node_id must not be 0xFFFF (GLOBAL_NA reserved)")
            node = SENode(
                nid, (px, py, pz), risk_state=risk, sub_system=sub, vel=(vx, vy, vz), phase=phase
            )
        else:
            nid, level, tcode, px, py, pz, r, g, b, nfl, p0 = struct.unpack_from(
                CORE_FMT, data, off
            )
            off += CORE_SIZE
            for v, name in ((px, "pos.x"), (py, "pos.y"), (pz, "pos.z"), (p0, "param0")):
                _check_finite(v, name)
            if nid == GLOBAL_NA:
                raise ProtocolError("node_id must not be 0xFFFF (GLOBAL_NA reserved)")
            node = SENode(
                nid,
                (px, py, pz),
                level=level,
                type_code=tcode,
                rgb=(r, g, b),
                node_flags=nfl,
                param0=p0,
            )
        if has_meta:
            freq, depth = struct.unpack_from("<fB", data, off)
            pad = data[off + 5 : off + 8]
            if pad != b"\x00\x00\x00":
                raise ProtocolError("Extended Meta pad must be zero")
            off += META_SIZE
            _check_finite(freq, "resonance_freq")
            node.resonance_freq = freq
            node.causal_depth = depth
        nodes.append(node)

    _assert_unique_node_ids(nodes)
    id_set = {n.node_id for n in nodes}

    constraints: List[Constraint] = []
    if has_ct:
        if off + 2 > len(data) - 4:
            raise ProtocolError("truncated constraint count")
        (m,) = struct.unpack_from("<H", data, off)
        off += 2
        if m > MAX_CONSTRAINTS:
            raise ProtocolError("too many constraints")
        for _ in range(m):
            if off + CONSTRAINT_SIZE > len(data) - 4:
                raise ProtocolError("truncated constraint entry")
            ctype, cflags, a, b, p0, p1, reserved = struct.unpack_from(
                "<BBHHffH", data, off
            )
            off += CONSTRAINT_SIZE
            if cflags != 0 or reserved != 0:
                raise ProtocolError("constraint reserved/cflags must be zero")
            _check_finite(p0, "constraint.param0")
            _check_finite(p1, "constraint.param1")
            if a != GLOBAL_NA and a not in id_set:
                raise ProtocolError(f"constraint node_a {a} out of SE set")
            if b != GLOBAL_NA and b not in id_set:
                raise ProtocolError(f"constraint node_b {b} out of SE set")
            constraints.append(Constraint(ctype, a, b, p0, p1))

    if off + 4 > len(data):
        raise ProtocolError("missing CRC32")
    if off + 4 != len(data):
        raise ProtocolError("trailing garbage bytes")

    crc_stored = struct.unpack_from("<I", data, off)[0]
    crc_calc = zlib.crc32(data[:off]) & 0xFFFFFFFF
    if crc_stored != crc_calc:
        raise ProtocolError("CRC32 mismatch (CRC-32/ISO-HDLC)")

    return DecodedFrame(
        version=ver,
        flags=flags,
        sequence_id=seq,
        nodes=nodes,
        constraints=constraints,
        raw_size=len(data),
    )


def demo() -> None:
    nodes = [
        SENode(0, (1.0, 0.0, 0.0)),
        SENode(1, (0.0, 1.0, 0.0)),
        SENode(2, (-1.0, 0.0, 0.0)),
        SENode(3, (0.0, -1.0, 0.0)),
    ]
    cons = [
        Constraint(0x01, 0, 1, 2.5),
        Constraint(0x02, GLOBAL_NA, GLOBAL_NA, 1.75),
    ]
    blob = encode_frame(nodes, constraints=cons)
    fr = decode_frame(blob)
    print("=== plod_spec_codec v1.1 demo ===")
    print(f"encoded {len(blob)} bytes  flags=0x{fr.flags:02x}  nodes={len(fr.nodes)}")
    print("strict encode + decode OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="P-LOD Spec v1.1 codec")
    ap.add_argument(
        "--demo",
        action="store_true",
        help="Run encode/decode demo (default if no other action)",
    )
    args = ap.parse_args()
    demo()
