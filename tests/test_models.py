import pytest

from printwatch.models import AppPreferences, AppState, CameraKind, CameraProfile, ValidationError


def test_camera_profile_round_trip() -> None:
    camera = CameraProfile(
        name="Resin Printer",
        url="http://192.168.1.69:3031/video",
        kind=CameraKind.ELEGOO_MJPEG,
        notes="Saturn camera",
    )
    restored = CameraProfile.from_dict(camera.to_dict())
    assert restored == camera


@pytest.mark.parametrize(
    "url",
    [
        "ftp://192.168.1.20/video",
        "http://",
        "http://user:password@192.168.1.20/video",
    ],
)
def test_camera_profile_rejects_unsafe_urls(url: str) -> None:
    with pytest.raises(ValidationError):
        CameraProfile(name="Printer", url=url).validate()


def test_cycle_interval_is_bounded() -> None:
    low = AppPreferences(cycle_interval_seconds=1)
    high = AppPreferences(cycle_interval_seconds=99999)
    low.normalize()
    high.normalize()
    assert low.cycle_interval_seconds == 5
    assert high.cycle_interval_seconds == 3600


def test_app_state_rejects_duplicate_ids() -> None:
    first = CameraProfile(name="One", url="http://one.local/video")
    second = CameraProfile(id=first.id, name="Two", url="http://two.local/video")
    with pytest.raises(ValidationError):
        AppState(cameras=[first, second]).validate()
