import pytest
from app.services.chunker import chunk_text, clean_text


def test_clean_text_collapses_whitespace():
    assert clean_text("hello   \n\n  world  ") == "hello world"


def test_clean_text_handles_empty_input():
    assert clean_text("") == ""
    assert clean_text(None) == ""


def test_chunk_text_returns_one_chunk_for_short_text():
    text = "This is a short document."
    chunks = chunk_text(text, chunk_size=1000, chunk_overlap=150)

    assert chunks == [text]


def test_chunk_text_splits_long_text_into_multiple_chunks():
    text = "word " * 500  # 2500 characters
    chunks = chunk_text(text, chunk_size=1000, chunk_overlap=150)

    assert len(chunks) > 1
    # every chunk should respect the size limit (with a little slack for
    # the word-boundary trimming)
    assert all(len(chunk) <= 1000 for chunk in chunks)


def test_chunk_text_overlap_repeats_boundary_content():
    text = "A" * 50 + " " + "B" * 50 + " " + "C" * 50
    chunks = chunk_text(text, chunk_size=60, chunk_overlap=20)

    assert len(chunks) >= 2
    # the tail of one chunk should reappear at the head of the next
    assert chunks[0][-10:] in chunks[1]


def test_chunk_text_empty_input_returns_no_chunks():
    assert chunk_text("", chunk_size=1000, chunk_overlap=150) == []
    assert chunk_text("   ", chunk_size=1000, chunk_overlap=150) == []


def test_chunk_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=100, chunk_overlap=100)
