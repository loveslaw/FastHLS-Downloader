"""
Unit tests for Segment Decryption
"""

import pytest
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from core.downloader import decrypt_segment


def test_decrypt_aes128_segment():
    key = b"16_BYTE_KEY_1234"
    iv = b"16_BYTE_IV_12345"
    plaintext = b"MPEG_TRANSPORT_STREAM_TEST_PACKET_CONTENT_123"

    # Pad with PKCS7
    pad_len = 16 - (len(plaintext) % 16)
    padded = plaintext + bytes([pad_len] * pad_len)

    # Encrypt
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    # Test decrypt_segment
    decrypted = decrypt_segment(ciphertext, key, iv)
    assert decrypted == plaintext
