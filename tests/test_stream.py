from printwatch.mjpeg import MjpegFrameParser


def jpeg(payload: bytes) -> bytes:
    return b"\xff\xd8" + payload + b"\xff\xd9"


def test_parser_extracts_frame_across_chunks() -> None:
    parser = MjpegFrameParser()
    assert parser.feed(b"--boundary\r\nContent-Type: image/jpeg\r\n\r\n\xff") == []
    assert parser.feed(b"\xd8frame-data\xff\xd9\r\n") == [jpeg(b"frame-data")]


def test_parser_extracts_multiple_frames() -> None:
    parser = MjpegFrameParser()
    frames = parser.feed(jpeg(b"one") + b"headers" + jpeg(b"two"))
    assert frames == [jpeg(b"one"), jpeg(b"two")]


def test_parser_ignores_leading_transport_headers() -> None:
    parser = MjpegFrameParser()
    assert parser.feed(b"Content-Length: 7\r\n\r\n" + jpeg(b"ok")) == [jpeg(b"ok")]


def test_parser_resets_an_oversized_incomplete_frame() -> None:
    parser = MjpegFrameParser(max_buffer_bytes=8)
    assert parser.feed(b"\xff\xd8" + b"x" * 20) == []
    assert parser.feed(jpeg(b"new")) == [jpeg(b"new")]


def test_parser_preserves_split_start_marker_when_trimming_junk() -> None:
    parser = MjpegFrameParser(max_buffer_bytes=4)
    assert parser.feed(b"junk\xff") == []
    assert parser.feed(b"\xd8x\xff\xd9") == [jpeg(b"x")]
