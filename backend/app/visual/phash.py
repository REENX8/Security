"""Pure-Python perceptual hash (dHash) — no image dependencies.

This module operates on a **grayscale pixel grid** (``list[list[int]]``, values
0-255), never on encoded images. Decoding a screenshot into a grid is the
renderer's job (``app/visual/renderer.py``); keeping the hash dependency-free
means the default/CI path never needs Pillow/OpenCV.

dHash (difference hash) is robust to scaling and compression and compares with a
simple Hamming distance, which makes it a good, cheap fingerprint for "is this
page a visual clone of a known template".
"""

from __future__ import annotations


def _resize(matrix: list[list[int]], out_w: int, out_h: int) -> list[list[int]]:
    """Nearest-neighbour downsample to ``out_w`` x ``out_h`` (pure Python)."""
    h = len(matrix)
    w = len(matrix[0]) if h else 0
    if h == 0 or w == 0:
        raise ValueError("empty pixel grid")
    out: list[list[int]] = []
    for y in range(out_h):
        sy = min(h - 1, y * h // out_h)
        src_row = matrix[sy]
        out.append([src_row[min(w - 1, x * w // out_w)] for x in range(out_w)])
    return out


def dhash(pixels: list[list[int]], size: int = 8) -> int:
    """Return a ``size*size``-bit difference hash of a grayscale pixel grid.

    The grid is resized to ``(size+1) x size``; each bit is 1 when a pixel is
    brighter than its right neighbour. ``size=8`` yields a 64-bit hash.
    """
    resized = _resize(pixels, size + 1, size)
    bits = 0
    pos = 0
    for row in resized:
        for x in range(size):
            if row[x] > row[x + 1]:
                bits |= 1 << pos
            pos += 1
    return bits


def hamming(a: int, b: int) -> int:
    """Number of differing bits between two hashes."""
    return (a ^ b).bit_count()


# A near-uniform image (blank/white page, or a render that never painted)
# produces a hash with very few or very many set bits. Such hashes carry no
# structural signal: a near-zero template would match any blank render and a
# blank page hash would match any low-bit template — both are false positives.
# Treat a hash as meaningful only when its set-bit count sits in this band.
_MIN_SET_BITS = 8
_MAX_SET_BITS = 56


def is_degenerate(h: int) -> bool:
    """True if a hash is too uniform to be a reliable fingerprint."""
    bits = h.bit_count()
    return bits < _MIN_SET_BITS or bits > _MAX_SET_BITS
