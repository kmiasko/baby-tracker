import pytest


@pytest.fixture(autouse=True)
def _isolated_home(tmp_path, monkeypatch):
    """Tests never read the user's ~/.baby-tracker (classifier.json, roi.json) or download the person model."""
    monkeypatch.setenv("BABY_TRACKER_HOME", str(tmp_path / "home"))
    from baby_tracker import seed

    monkeypatch.setattr(seed, "make_seeder", lambda cfg: None)
