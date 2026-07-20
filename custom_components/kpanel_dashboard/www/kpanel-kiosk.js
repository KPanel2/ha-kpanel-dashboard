/**
 * KPanel kiosk chrome — hide HA header/sidebar.
 * Scope: chrome only. Auth is handled by the integration + KPanel client.
 */
(function kpanelKiosk(global) {
  const STYLE_ID = "kpanel-kiosk-style";

  function parseFlags(search) {
    const params = new URLSearchParams(search.startsWith("?") ? search : `?${search}`);
    const rawKiosk = params.get("kiosk");
    const kiosk =
      params.has("kiosk") &&
      (rawKiosk === null ||
        rawKiosk === "" ||
        rawKiosk === "true" ||
        rawKiosk === "1");

    const flag = (name) => {
      if (!params.has(name)) return false;
      const value = params.get(name);
      return value === null || value === "" || value === "true" || value === "1";
    };

    return {
      hideHeader: kiosk || flag("hide_header"),
      hideSidebar: kiosk || flag("hide_sidebar"),
    };
  }

  function buildCss(flags) {
    const rules = [];
    if (flags.hideHeader) {
      rules.push(
        "home-assistant-main::part(header), app-toolbar, .header { display: none !important; }"
      );
    }
    if (flags.hideSidebar) {
      rules.push(
        "home-assistant-main::part(sidebar), ha-sidebar, .sidebar { display: none !important; }",
        "home-assistant-main { --mdc-drawer-width: 0 !important; }"
      );
    }
    return rules.join("\n");
  }

  function applyKioskChrome(flags, doc) {
    const documentRef = doc || document;
    let style = documentRef.getElementById(STYLE_ID);
    const css = buildCss(flags);
    if (!css) {
      if (style) style.remove();
      return false;
    }
    if (!style) {
      style = documentRef.createElement("style");
      style.id = STYLE_ID;
      documentRef.head.appendChild(style);
    }
    style.textContent = css;
    return true;
  }

  function run(search, doc) {
    return applyKioskChrome(parseFlags(search), doc);
  }

  const api = { parseFlags, buildCss, applyKioskChrome, run };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  global.KPanelKiosk = api;

  if (typeof document !== "undefined" && document.readyState !== undefined) {
    const start = () => run(global.location ? global.location.search : "");
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", start);
    } else {
      start();
    }
  }
})(typeof globalThis !== "undefined" ? globalThis : this);
