"""Constants for the KPanel Dashboard Home Assistant integration."""

from __future__ import annotations

DOMAIN = "kpanel_dashboard"

CONF_USER_ID = "user_id"
CONF_USERNAME = "username"
CONF_DASHBOARD_PATH = "dashboard_path"
CONF_BINDING_SECRET = "binding_secret"
CONF_HIDE_HEADER = "hide_header"
CONF_HIDE_SIDEBAR = "hide_sidebar"
CONF_REFRESH_TOKEN_ID = "refresh_token_id"

DEFAULT_DASHBOARD_PATH = "/lovelace/kiosk"
CLIENT_NAME = "KPanel Dashboard"

BOOTSTRAP_PATH = "/api/kpanel_dashboard/bootstrap"
BINDING_SECRET_HEADER = "X-KPanel-Binding-Secret"

SERVICE_ROTATE_TOKENS = "rotate_tokens"

# Bootstrap rate limit (per binding secret)
BOOTSTRAP_RATE_LIMIT_MAX = 30
BOOTSTRAP_RATE_LIMIT_WINDOW_SECONDS = 60.0
