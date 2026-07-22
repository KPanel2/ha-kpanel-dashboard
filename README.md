# KPanel Dashboard (Home Assistant)

<p align="center">
  <img src="images/logo.png" alt="KPanel" width="280" />
</p>

HACS custom integration that pairs with [KPanel2](https://github.com/KPanel2/kpanel2) to auto-authenticate a Pi kiosk browser into a Home Assistant dashboard.

Brand icons/logos under `custom_components/kpanel_dashboard/brand/` are generated from the KPanel2 [`brand_kit`](https://github.com/KPanel2/kpanel2/tree/main/brand_kit) (HA 2026.3+ local brands proxy). Regenerate with:

```bash
pip install pillow numpy
python3 scripts/sync_brand_from_kit.py
```

## What this provides

- **Config flow** — select an HA user and dashboard path; generates a binding secret
- **Token minting** — creates a dedicated refresh token for the selected user (`AuthTokenService`)
- **Bootstrap API** — `GET /api/kpanel_dashboard/bootstrap` with header `X-KPanel-Binding-Secret` returns `{ hass_url, hass_tokens, dashboard_url, kiosk, ready: true }`
- **Rotate service** — `kpanel_dashboard.rotate_tokens` revokes and remints the refresh token
- **Kiosk chrome** — auto-loaded module hides header/sidebar when `?kiosk` / `?hide_header` / `?hide_sidebar` is present

Auth is **not** done in Lovelace JS. Tokens are minted by this integration and injected by the KPanel client via Chrome DevTools Protocol (`localStorage.hassTokens`).

## Install (HACS)

1. Add this repo as a custom repository (Integration).
2. Install **KPanel Dashboard**.
3. Restart Home Assistant.
4. Settings → Devices & Services → Add Integration → **KPanel Dashboard**.

## Security model

- Never put refresh/LLAT secrets in the public dashboard URL.
- Prefer a non-admin kiosk user with a locked-down dashboard.
- Protect the bootstrap endpoint with the binding secret (`X-KPanel-Binding-Secret`).
- Anyone with physical access to the panel can use that user’s HA session (same class of risk as `trusted_networks` kiosks).

### Fallback

HA `trusted_networks` + `trusted_users` + `allow_bypass_login`, and/or KPanel’s persistent Chromium profile.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
node --test tests/js/*.test.js
```

## Status

Phases 2–4 complete in this submodule: config flow (with binding-secret confirm + options rotate), token minting, ready bootstrap, rotate service, rate limit, kiosk chrome JS. KPanel2 portal binding + client CDP seeder live in the parent repo — see `.cursor/plans/ha_kpanel_auth_bridge.plan.md`.
