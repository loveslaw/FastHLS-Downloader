"""
Unit tests for TS Segment Stitcher
"""

import os
import pytest
from core.stitcher import stitch_segments


def test_stitch_segments_ordering_and_output(tmp_path):
    chunks = [
        (2, b"CHUNK_THREE_DATA"),
        (0, b"CHUNK_ONE_DATA"),
        (1, b"CHUNK_TWO_DATA"),
    ]

    out_file = tmp_path / "combined.ts"
    result_path = stitch_segments(chunks, str(out_file))

    assert os.path.exists(result_path)
    with open(result_path, "rb") as f:
        data = f.read()

    expected = b"CHUNK_ONE_DATACHUNK_TWO_DATACHUNK_THREE_DATA"
    assert data == expected
