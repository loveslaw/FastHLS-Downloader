"""
M3U8 Playlist & Stream Manifest Parser
Extracts segment URIs, encryption keys, durations, and resolves relative paths.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple
from urllib.parse import urljoin


@dataclass
class HLSSegment:
    index: int
    duration: float
    url: str
    key_uri: Optional[str] = None
    key_iv: Optional[bytes] = None


@dataclass
class HLSPlaylist:
    is_master: bool
    segments: List[HLSSegment]
    variants: List[Tuple[int, str]]  # [(bandwidth, url)]
    target_duration: int = 10


def parse_m3u8(content: str, base_url: str = "") -> HLSPlaylist:
    """Parses M3U8 text into an HLSPlaylist object."""
    if not content.strip().startswith("#EXTM3U"):
        raise ValueError("Invalid manifest: Missing #EXTM3U header.")

    lines = [line.strip() for line in content.splitlines() if line.strip()]

    is_master = any(line.startswith("#EXT-X-STREAM-INF") for line in lines)
    variants = []
    segments = []
    target_duration = 10

    if is_master:
        current_bw = 0
        for i, line in enumerate(lines):
            if line.startswith("#EXT-X-STREAM-INF"):
                match = re.search(r"BANDWIDTH=(\d+)", line)
                current_bw = int(match.group(1)) if match else 0
            elif not line.startswith("#") and current_bw > 0:
                variant_url = urljoin(base_url, line)
                variants.append((current_bw, variant_url))
                current_bw = 0
        variants.sort(key=lambda x: x[0], reverse=True)
        return HLSPlaylist(is_master=True, segments=[], variants=variants)

    # Media Playlist parsing
    current_key_uri = None
    current_key_iv = None
    current_duration = 0.0
    segment_idx = 0

    for line in lines:
        if line.startswith("#EXT-X-TARGETDURATION:"):
            target_duration = int(line.split(":")[1])

        elif line.startswith("#EXT-X-KEY:"):
            # Parse AES-128 key parameters
            method_match = re.search(r"METHOD=([^,\s]+)", line)
            if method_match and method_match.group(1).upper() == "AES-128":
                uri_match = re.search(r'URI="([^"]+)"', line)
                if uri_match:
                    current_key_uri = urljoin(base_url, uri_match.group(1))

                iv_match = re.search(r"IV=0x([0-9a-fA-F]+)", line)
                if iv_match:
                    current_key_iv = bytes.fromhex(iv_match.group(1))
            elif method_match and method_match.group(1).upper() == "NONE":
                current_key_uri = None
                current_key_iv = None

        elif line.startswith("#EXTINF:"):
            duration_match = re.search(r"#EXTINF:([0-9.]+)", line)
            if duration_match:
                current_duration = float(duration_match.group(1))

        elif not line.startswith("#"):
            seg_url = urljoin(base_url, line)
            segments.append(
                HLSSegment(
                    index=segment_idx,
                    duration=current_duration,
                    url=seg_url,
                    key_uri=current_key_uri,
                    key_iv=current_key_iv or segment_idx.to_bytes(16, "big"),
                )
            )
            segment_idx += 1
            current_duration = 0.0

    return HLSPlaylist(
        is_master=False,
        segments=segments,
        variants=[],
        target_duration=target_duration,
    )
