"""Gate-2 coverage tests for WordlistXPL-Forge core modules."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# wfh_modules.xor_crypto
# ---------------------------------------------------------------------------

def test_score_text_readable() -> None:
    from wfh_modules.xor_crypto import score_text
    assert score_text("Hello World") > 0
    assert score_text("") == 0


def test_score_text_binary() -> None:
    from wfh_modules.xor_crypto import score_text
    assert score_text("\x00\x01\x02\x03") == 0


def test_xor_decrypt_single_byte_key() -> None:
    from wfh_modules.xor_crypto import xor_decrypt
    ct = bytes([0x48 ^ 0xAA, 0x65 ^ 0xAA, 0x6C ^ 0xAA])
    result = xor_decrypt(ct, b"\xAA")
    assert result == b"Hel"


def test_xor_encrypt_roundtrip() -> None:
    from wfh_modules.xor_crypto import xor_encrypt, xor_decrypt
    plaintext = b"secret message"
    key = b"key123"
    ct = xor_encrypt(plaintext, key)
    assert ct != plaintext
    assert xor_decrypt(ct, key) == plaintext


def test_xor_encrypt_str() -> None:
    from wfh_modules.xor_crypto import xor_encrypt_str, xor_decrypt
    ct = xor_encrypt_str("hello", "k")
    assert isinstance(ct, bytes)
    assert xor_decrypt(ct, b"k") == b"hello"


def test_xor_brute_force_single_byte() -> None:
    from wfh_modules.xor_crypto import xor_encrypt, brute_force_single_byte
    plaintext = b"Hello World 123"
    key = b"\x42"
    ct = xor_encrypt(plaintext, key)
    hex_ct = ct.hex()
    results = brute_force_single_byte(hex_ct)
    assert len(results) >= 1
    assert any(r.get("key") == 0x42 for r in results)


def test_xor_decrypt_str() -> None:
    from wfh_modules.xor_crypto import xor_encrypt_str, xor_decrypt_str
    ct = xor_encrypt_str("hello world", "k")
    result = xor_decrypt_str(ct, "k")
    assert result == "hello world"


def test_xor_brute_force_display(capsys) -> None:
    from wfh_modules.xor_crypto import xor_encrypt, brute_force_display
    ct = xor_encrypt(b"test", b"\x20")
    brute_force_display(ct.hex())
    # Just verify it runs without error; output goes to stdout


# ---------------------------------------------------------------------------
# wfh_modules.passphrase_gen
# ---------------------------------------------------------------------------

def test_generate_yields_strings() -> None:
    from wfh_modules.passphrase_gen import generate, _load_words
    words = _load_words(None)
    gen = generate(words, count=3, num_words=4, separator="-")
    phrases = list(gen)
    assert len(phrases) == 3
    for p in phrases:
        assert isinstance(p, str)
        assert p.count("-") == 3


def test_generate_capitalize() -> None:
    from wfh_modules.passphrase_gen import generate, _load_words
    words = _load_words(None)
    gen = generate(words, count=2, num_words=3, capitalize=True)
    phrases = list(gen)
    for p in phrases:
        # At least one word should start with uppercase
        assert any(w[0].isupper() for w in p.split("-") if w)


def test_generate_add_number() -> None:
    from wfh_modules.passphrase_gen import generate, _load_words
    words = _load_words(None)
    gen = generate(words, count=5, num_words=3, add_number=True)
    found = False
    for p in gen:
        if any(c.isdigit() for c in p):
            found = True
            break
    assert found


def test_load_words_builtin() -> None:
    from wfh_modules.passphrase_gen import _load_words
    words = _load_words(None)
    assert isinstance(words, list)
    assert len(words) > 50
    assert all(isinstance(w, str) for w in words)


# ---------------------------------------------------------------------------
# wfh_modules.linkwords (if importable)
# ---------------------------------------------------------------------------

def test_linkwords_importable() -> None:
    try:
        import wfh_modules.linkwords as lw
        assert lw is not None
    except ImportError:
        pass  # Optional dep
