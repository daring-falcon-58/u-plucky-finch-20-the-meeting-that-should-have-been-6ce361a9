#!/usr/bin/env python3
"""The Meeting That Should Have Been an Email — make.fun entry.

Writes one line, a single joke about a meeting that should have been an
email, to $MAKEFUN_OUTPUT_DIR/entry.txt (falling back to /output/entry.txt).

The line (95 characters, 95 bytes, no trailing newline):
    Only one person had read the email, so we spent an hour punishing him by
    making him present it.

Chosen from 38 candidates scored 0-5 against each of the five published judge
criteria (see candidates.md in the work dir; full table and head-to-head notes
there). Winner scored 24/25; the three runner-ups scored 23/25. No live-judge
A/B was run: the shared OpenRouter key is exhausted (HTTP 402), so selection is
structured manual scoring against the published brief — stated honestly in
README.md, with no judge numbers claimed.

Deterministic, no network, no randomness: two runs produce byte-identical
output. See README.md for the methodology.
"""

import hashlib
import os
import re

ENTRY = "Only one person had read the email, so we spent an hour punishing him by making him present it."

# sha256 of ENTRY encoded as UTF-8 (95 bytes, no trailing newline). The
# write-back check below recomputes the digest of the bytes on disk and
# compares it to this value, so even a silent one-byte change fails loudly.
EXPECTED_SHA256 = "2187d7d759ae9f390198efcae05f49db617087b8ce7f9fe82cfe2f1b1884347e"

# The competition gate is 1-200 characters, one line, not only whitespace.
# The brief's own constraints, enforced here at import time so a bad edit
# fails loudly instead of silently writing an entry the grader rejects.
MAX_CHARS = 200
MAX_SENTENCES = 1
BANNED_PATTERNS = (
    re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"),  # control characters
    re.compile(r"https?://"),                        # links: the line stands alone
    re.compile(r"[*#`_~]"),                         # markdown formatting
    re.compile(r"\[[^\]]*\]"),                      # stage directions like [sighs]
)


def validate(entry: str) -> None:
    """Reject any entry that breaks the brief's constraints, with a clear error.

    Each message names the constraint that failed and the offending value, so
    a bad edit points straight at what to fix instead of a bare traceback.
    """
    if not entry or not entry.strip():
        raise ValueError(
            "entry is empty or only whitespace — the gate needs 1-200 characters"
        )
    if not 1 <= len(entry) <= MAX_CHARS:
        raise ValueError(
            f"entry length {len(entry)} chars is outside the 1-{MAX_CHARS} gate"
        )
    if "\n" in entry or "\r" in entry:
        raise ValueError(
            "entry must be exactly one line — it contains a newline character"
        )
    sentences = [s for s in re.split(r"[.!?]+", entry) if s.strip()]
    if len(sentences) > MAX_SENTENCES:
        raise ValueError(
            f"entry has {len(sentences)} sentences, over the {MAX_SENTENCES}-sentence cap"
        )
    for pattern in BANNED_PATTERNS:
        match = pattern.search(entry)
        if match:
            raise ValueError(
                f"entry contains banned text {match.group(0)!r} "
                f"(pattern {pattern.pattern!r}) — remove it before submitting"
            )


validate(ENTRY)


def write_entry(path: str) -> bytes:
    """Write ENTRY to path as exact bytes and return what was written.

    Byte-exactness is the whole point: the grader reads entry.txt as bytes,
    so the file must be ENTRY encoded as UTF-8 with no trailing newline and
    no newline translation. That is why the file is opened with
    ``newline=""`` — on any platform, Python must not rewrite ``\n`` — and
    why the caller verifies the bytes on disk instead of trusting the write.
    """
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(ENTRY)
    # Re-read from disk rather than trusting the write buffer: a partial
    # write or encoding surprise only shows up in the bytes on disk.
    return open(path, "rb").read()


def verify_written(path: str, written: bytes) -> None:
    """Fail loudly unless the bytes on disk are exactly ENTRY, byte for byte."""
    if written != ENTRY.encode("utf-8"):
        raise OSError(f"entry.txt at {path} does not match the entry")
    digest = hashlib.sha256(written).hexdigest()
    if digest != EXPECTED_SHA256:
        raise OSError(
            f"entry.txt sha256 {digest} != expected {EXPECTED_SHA256}"
        )


def main() -> None:
    # /output is the grader sandbox's default output dir; MAKEFUN_OUTPUT_DIR
    # overrides it when the harness sets one.
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    written = write_entry(path)
    verify_written(path, written)


if __name__ == "__main__":
    main()
