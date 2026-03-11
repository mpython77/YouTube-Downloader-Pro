"""
Tests for utils/validators.py — URL validation tests.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from utils.validators import (
    is_valid_youtube_url, is_playlist_url,
    extract_video_id, sanitize_filename,
)


class TestIsValidYoutubeUrl:
    """YouTube URL validation tests."""

    # Valid URLs
    def test_standard_url(self):
        assert is_valid_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_short_url(self):
        assert is_valid_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True

    def test_mobile_url(self):
        assert is_valid_youtube_url("https://m.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_music_url(self):
        assert is_valid_youtube_url("https://music.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_shorts_url(self):
        assert is_valid_youtube_url("https://www.youtube.com/shorts/dQw4w9WgXcQ") is True

    def test_embed_url(self):
        assert is_valid_youtube_url("https://www.youtube.com/embed/dQw4w9WgXcQ") is True

    def test_live_url(self):
        assert is_valid_youtube_url("https://www.youtube.com/live/dQw4w9WgXcQ") is True

    def test_playlist_url(self):
        assert is_valid_youtube_url("https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf") is True

    # Invalid URLs
    def test_empty_string(self):
        assert is_valid_youtube_url("") is False

    def test_none(self):
        assert is_valid_youtube_url(None) is False

    def test_random_text(self):
        assert is_valid_youtube_url("not a url") is False

    def test_other_domain(self):
        assert is_valid_youtube_url("https://www.google.com") is False

    def test_no_scheme(self):
        assert is_valid_youtube_url("youtube.com/watch?v=test") is False

    def test_no_video_id(self):
        assert is_valid_youtube_url("https://www.youtube.com/watch") is False

    def test_vimeo(self):
        assert is_valid_youtube_url("https://vimeo.com/123456") is False

    def test_http_scheme(self):
        assert is_valid_youtube_url("http://www.youtube.com/watch?v=dQw4w9WgXcQ") is True


class TestIsPlaylistUrl:
    """Playlist URL detection tests."""

    def test_playlist_url(self):
        assert is_playlist_url("https://www.youtube.com/playlist?list=PLtest123") is True

    def test_video_with_playlist(self):
        assert is_playlist_url("https://www.youtube.com/watch?v=test&list=PLtest") is True

    def test_single_video(self):
        assert is_playlist_url("https://www.youtube.com/watch?v=test123456") is False

    def test_empty(self):
        assert is_playlist_url("") is False

    def test_none(self):
        assert is_playlist_url(None) is False


class TestExtractVideoId:
    """Video ID extraction tests."""

    def test_standard_url(self):
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url(self):
        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_embed_url(self):
        assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_empty(self):
        assert extract_video_id("") is None

    def test_none(self):
        assert extract_video_id(None) is None

    def test_invalid_url(self):
        assert extract_video_id("https://google.com") is None


class TestSanitizeFilename:
    """Filename sanitization tests."""

    def test_normal_filename(self):
        assert sanitize_filename("My Video Title") == "My Video Title"

    def test_special_characters(self):
        result = sanitize_filename('Video: "Best" <Top> | File?')
        assert ":" not in result
        assert '"' not in result
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result
        assert "?" not in result

    def test_empty_string(self):
        assert sanitize_filename("") == "untitled"

    def test_none_like(self):
        assert sanitize_filename(None) == "untitled"

    def test_max_length(self):
        long_name = "A" * 300
        result = sanitize_filename(long_name, max_length=200)
        assert len(result) <= 200

    def test_trailing_dots(self):
        result = sanitize_filename("filename...")
        assert not result.endswith(".")

    def test_leading_spaces(self):
        result = sanitize_filename("  filename  ")
        assert not result.startswith(" ")
        assert not result.endswith(" ")
