from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4


class CameraKind(StrEnum):
    ELEGOO_MJPEG = "elegoo_mjpeg"
    CUSTOM_HTTP = "custom_http"


class ValidationError(ValueError):
    """Raised when a camera profile is unsafe or incomplete."""


@dataclass(slots=True)
class CameraProfile:
    name: str
    url: str
    kind: CameraKind = CameraKind.CUSTOM_HTTP
    enabled: bool = True
    notes: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def validate(self) -> None:
        self.name = self.name.strip()
        self.url = self.url.strip()
        self.notes = self.notes.strip()

        if not self.name:
            raise ValidationError("Camera name is required.")
        if len(self.name) > 80:
            raise ValidationError("Camera name must be 80 characters or fewer.")

        parsed = urlsplit(self.url)
        if parsed.scheme not in {"http", "https"}:
            raise ValidationError("Stream URL must use http:// or https://.")
        if not parsed.hostname:
            raise ValidationError("Stream URL must include a host name or IP address.")
        if parsed.username or parsed.password:
            raise ValidationError(
                "Credentials embedded in URLs are not stored. Use a camera without URL credentials."
            )
        try:
            parsed.port
        except ValueError as error:
            raise ValidationError("Stream URL port must be a number from 1 through 65535.") from error

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CameraProfile:
        profile = cls(
            id=str(data.get("id") or uuid4()),
            name=str(data.get("name", "")),
            url=str(data.get("url", "")),
            kind=CameraKind(data.get("kind", CameraKind.CUSTOM_HTTP.value)),
            enabled=bool(data.get("enabled", True)),
            notes=str(data.get("notes", "")),
        )
        profile.validate()
        return profile


@dataclass(slots=True)
class AppPreferences:
    cycle_enabled: bool = False
    cycle_interval_seconds: int = 15
    selected_camera_id: str | None = None
    onboarding_completed: bool = False

    def normalize(self) -> None:
        self.cycle_interval_seconds = max(5, min(3600, int(self.cycle_interval_seconds)))

    def to_dict(self) -> dict[str, Any]:
        self.normalize()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppPreferences:
        preferences = cls(
            cycle_enabled=bool(data.get("cycle_enabled", False)),
            cycle_interval_seconds=int(data.get("cycle_interval_seconds", 15)),
            selected_camera_id=data.get("selected_camera_id"),
            onboarding_completed=bool(data.get("onboarding_completed", False)),
        )
        preferences.normalize()
        return preferences


@dataclass(slots=True)
class AppState:
    cameras: list[CameraProfile] = field(default_factory=list)
    preferences: AppPreferences = field(default_factory=AppPreferences)
    schema_version: int = 1

    def validate(self) -> None:
        ids: set[str] = set()
        for camera in self.cameras:
            camera.validate()
            if camera.id in ids:
                raise ValidationError(f"Duplicate camera id: {camera.id}")
            ids.add(camera.id)
        self.preferences.normalize()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "cameras": [camera.to_dict() for camera in self.cameras],
            "preferences": self.preferences.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppState:
        schema_version = int(data.get("schema_version", 1))
        if schema_version != 1:
            raise ValidationError(f"Unsupported configuration schema: {schema_version}")
        state = cls(
            schema_version=schema_version,
            cameras=[CameraProfile.from_dict(item) for item in data.get("cameras", [])],
            preferences=AppPreferences.from_dict(data.get("preferences", {})),
        )
        state.validate()
        return state
