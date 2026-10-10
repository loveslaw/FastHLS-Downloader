"""
Concurrent TS Segment Downloader & AES-128 Decryptor
Pulls segments across multi-threaded workers with automatic retry backoff.
"""

import concurrent.futures
import time
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from core.parser import HLSSegment


def decrypt_segment(encrypted_data: bytes, key: bytes, iv: bytes) -> bytes:
    """Decrypts AES-128-CBC encrypted MPEG-TS segment data."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted_data) + decryptor.finalize()

    # PKCS7 padding removal if present
    pad_len = decrypted[-1]
    if 0 < pad_len <= 16:
        # Check padding validity
        if decrypted[-pad_len:] == bytes([pad_len] * pad_len):
            return decrypted[:-pad_len]
    return decrypted


def fetch_url(url: str, timeout: int = 15, retries: int = 3) -> bytes:
    """Fetches raw bytes from a URL with retry backoff."""
    headers = {"User-Agent": "FastHLS-Downloader/1.0"}
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(0.5 * (attempt + 1))
    return b""


class SegmentDownloader:
    def __init__(self, concurrency: int = 16, retries: int = 3):
        self.concurrency = concurrency
        self.retries = retries
        self._key_cache: Dict[str, bytes] = {}

    def get_key(self, key_uri: str) -> bytes:
        if key_uri not in self._key_cache:
            self._key_cache[key_uri] = fetch_url(key_uri, retries=self.retries)
        return self._key_cache[key_uri]

    def download_segment(self, segment: HLSSegment) -> Tuple[int, bytes]:
        """Downloads a single segment and decrypts if an AES-128 key is specified."""
        raw_bytes = fetch_url(segment.url, retries=self.retries)

        if segment.key_uri and segment.key_iv:
            key = self.get_key(segment.key_uri)
            data = decrypt_segment(raw_bytes, key, segment.key_iv)
        else:
            data = raw_bytes

        return segment.index, data

    def download_all(
        self,
        segments: List[HLSSegment],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Tuple[int, bytes]]:
        """Downloads all segments concurrently and returns them in original order."""
        results: List[Tuple[int, bytes]] = []
        total = len(segments)
        completed = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            future_map = {executor.submit(self.download_segment, seg): seg for seg in segments}
            for future in concurrent.futures.as_completed(future_map):
                idx, data = future.result()
                results.append((idx, data))
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

        results.sort(key=lambda x: x[0])
        return results
