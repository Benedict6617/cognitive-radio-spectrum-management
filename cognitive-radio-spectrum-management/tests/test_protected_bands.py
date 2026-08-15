from app.services.protected_bands import Band, is_protected


def test_overlapping_band_detected():
    bands = [Band("Test Public Safety", 420_000_000, 425_000_000, "public-safety")]
    result = is_protected(419_000_000, 421_000_000, bands)
    assert result is not None
    assert result.name == "Test Public Safety"


def test_non_overlapping_band_not_flagged():
    bands = [Band("Test Public Safety", 420_000_000, 425_000_000, "public-safety")]
    result = is_protected(430_000_000, 435_000_000, bands)
    assert result is None


def test_adjacent_but_not_overlapping_band():
    bands = [Band("Test Band", 420_000_000, 425_000_000, "public-safety")]
    # [425_000_000, 430_000_000) starts exactly where the band ends -> no overlap
    result = is_protected(425_000_000, 430_000_000, bands)
    assert result is None
