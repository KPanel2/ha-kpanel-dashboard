"""Domain model for kiosk / dashboard binding configuration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .const import (
    CONF_BINDING_SECRET,
    CONF_DASHBOARD_PATH,
    CONF_HIDE_HEADER,
    CONF_HIDE_SIDEBAR,
    CONF_REFRESH_TOKEN_ID,
    CONF_USER_ID,
    CONF_USERNAME,
    DEFAULT_DASHBOARD_PATH,
)


@dataclass(frozen=True, slots=True)
class KioskConfig:
    """Immutable config stored on a config entry."""

    user_id: str
    username: str | None
    dashboard_path: str
    binding_secret: str | None
    hide_header: bool
    hide_sidebar: bool
    refresh_token_id: str | None = None

    @staticmethod
    def normalize_dashboard_path(path: str) -> str:
        cleaned = (path or "").strip()
        if not cleaned:
            raise ValueError("dashboard_path is required")
        if not cleaned.startswith("/"):
            cleaned = f"/{cleaned}"
        return cleaned

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> KioskConfig:
        user_id = data.get(CONF_USER_ID)
        if not user_id or not str(user_id).strip():
            raise ValueError("user_id is required")
        raw_path = data.get(CONF_DASHBOARD_PATH, DEFAULT_DASHBOARD_PATH)
        return cls(
            user_id=str(user_id).strip(),
            username=data.get(CONF_USERNAME),
            dashboard_path=cls.normalize_dashboard_path(
                str(raw_path if raw_path is not None else DEFAULT_DASHBOARD_PATH)
            ),
            binding_secret=data.get(CONF_BINDING_SECRET),
            hide_header=bool(data.get(CONF_HIDE_HEADER, True)),
            hide_sidebar=bool(data.get(CONF_HIDE_SIDEBAR, True)),
            refresh_token_id=data.get(CONF_REFRESH_TOKEN_ID),
        )

    def to_entry_data(self) -> dict[str, Any]:
        return asdict(self)
