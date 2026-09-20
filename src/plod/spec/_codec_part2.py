
def encode_frame(
    nodes: Sequence[SENode],
    *,
    constraints: Optional[Sequence[Constraint]] = None,
    embodied: bool = False,
    extended_meta: bool = False,
    version: int = VERSION_V11,
    sequence_id: int = 1,
) -> bytes:
    if version not in (VERSION_V10, VERSION_V11):
        raise ProtocolError(f"version must be 0x10 or 0x11, got {version:#x}")
    _require_int_range(sequence_id, 0, MAX_U16, "sequence_id")
    if len(nodes) > MAX_SE_NODES:
        raise ProtocolError("MAX_SE_NODES exceeded")
    _assert_unique_node_ids(nodes)

    cons = list(constraints or [])
    if version == VERSION_V10 and (cons or extended_meta):
        raise ProtocolError("v1.0 forbids Constraint Table and Extended Meta")
    if len(cons) > MAX_CONSTRAINTS:
        raise ProtocolError("MAX_CONSTRAINTS exceeded")

    for n in nodes:
        _validate_node_for_encode(n, embodied)

    id_set = {n.node_id for n in nodes}
    for c in cons:
        _require_int_range(c.ctype, 0, 255, "constraint_type")
        _check_finite(c.param0, "constraint.param0")
        _check_finite(c.param1, "constraint.param1")
        if c.node_a != GLOBAL_NA and c.node_a not in id_set:
            raise ProtocolError(f"constraint node_a {c.node_a} out of SE set")
        if c.node_b != GLOBAL_NA and c.node_b not in id_set:
            raise ProtocolError(f"constraint node_b {c.node_b} out of SE set")
        if c.node_a != GLOBAL_NA:
            _require_int_range(c.node_a, 0, MAX_NODE_ID, "constraint.node_a")
        if c.node_b != GLOBAL_NA:
            _require_int_range(c.node_b, 0, MAX_NODE_ID, "constraint.node_b")

    flags = 0
    if cons:
        flags |= FLAG_HAS_CONSTRAINT_TABLE
    if embodied:
        flags |= FLAG_IS_EMBODIED_PROFILE
    if extended_meta:
        flags |= FLAG_HAS_EXTENDED_META

    body = bytearray()
    body += struct.pack("<HBBHH", MAGIC, version, flags, len(nodes), sequence_id)

    for n in nodes:
        if embodied:
            body += struct.pack(
                "<HBB3f3ff",
                n.node_id,
                n.risk_state,
                n.sub_system,
                float(n.pos[0]),
                float(n.pos[1]),
                float(n.pos[2]),
                float(n.vel[0]),
                float(n.vel[1]),
                float(n.vel[2]),
                float(n.phase),
            )
        else:
            body += struct.pack(
                CORE_FMT,
                n.node_id,
                n.level,
                n.type_code,
                float(n.pos[0]),
                float(n.pos[1]),
                float(n.pos[2]),
                int(n.rgb[0]),
                int(n.rgb[1]),
                int(n.rgb[2]),
                n.node_flags,
                float(n.param0),
            )
        if extended_meta:
            body += struct.pack("<fBxxx", float(n.resonance_freq), n.causal_depth)

    if cons:
        body += struct.pack("<H", len(cons))
        for c in cons:
            body += struct.pack(
                "<BBHHffH",
                c.ctype,
                0,
                c.node_a,
                c.node_b,
                float(c.param0),
                float(c.param1),
                0,
            )

    if len(body) + 4 > MAX_FRAME_SIZE:
        raise ProtocolError("MAX_FRAME_SIZE exceeded")

    crc = zlib.crc32(bytes(body)) & 0xFFFFFFFF
    body += struct.pack("<I", crc)
    return bytes(body)

