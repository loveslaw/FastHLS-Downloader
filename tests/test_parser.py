"""
Unit tests for M3U8 Manifest Parser
"""

import pytest
from core.parser import parse_m3u8


SAMPLE_MASTER_M3U8 = """#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720
720p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2560000,RESOLUTION=1920x1080
1080p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
360p.m3u8
"""

SAMPLE_MEDIA_M3U8 = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXTINF:9.009,
segment_0.ts
#EXTINF:9.009,
segment_1.ts
#EXTINF:5.230,
segment_2.ts
#EXT-X-ENDLIST
"""

SAMPLE_AES128_M3U8 = """#EXTM3U
#EXT-X-TARGETDURATION:10
#EXT-X-KEY:METHOD=AES-128,URI="https://example.com/enc.key",IV=0x000102030405060708090a0b0c0d0e0f
#EXTINF:10.0,
chunk_0.ts
#EXTINF:10.0,
chunk_1.ts
"""


def test_parse_master_playlist():
    playlist = parse_m3u8(SAMPLE_MASTER_M3U8, base_url="https://stream.net/live/")
    assert playlist.is_master is True
    assert len(playlist.variants) == 3
    # Top bandwidth should be sorted first (2560000)
    top_bw, top_url = playlist.variants[0]
    assert top_bw == 2560000
    assert top_url == "https://stream.net/live/1080p.m3u8"


def test_parse_media_playlist():
    playlist = parse_m3u8(SAMPLE_MEDIA_M3U8, base_url="https://stream.net/hls/")
    assert playlist.is_master is False
    assert len(playlist.segments) == 3
    assert playlist.segments[0].index == 0
    assert playlist.segments[0].duration == 9.009
    assert playlist.segments[0].url == "https://stream.net/hls/segment_0.ts"
    assert playlist.segments[2].duration == 5.230


def test_parse_aes128_key_parameters():
    playlist = parse_m3u8(SAMPLE_AES128_M3U8, base_url="https://stream.net/")
    assert len(playlist.segments) == 2
    seg0 = playlist.segments[0]
    assert seg0.key_uri == "https://example.com/enc.key"
    assert seg0.key_iv == bytes.fromhex("000102030405060708090a0b0c0d0e0f")
