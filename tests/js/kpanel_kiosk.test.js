const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");

const {
  parseFlags,
  buildCss,
  applyKioskChrome,
} = require(path.join(
  __dirname,
  "..",
  "..",
  "custom_components",
  "kpanel_dashboard",
  "www",
  "kpanel-kiosk.js"
));

test("parseFlags: bare ?kiosk enables both", () => {
  assert.deepEqual(parseFlags("?kiosk"), {
    hideHeader: true,
    hideSidebar: true,
  });
});

test("parseFlags: hide_header only", () => {
  assert.deepEqual(parseFlags("?hide_header=true"), {
    hideHeader: true,
    hideSidebar: false,
  });
});

test("parseFlags: hide_sidebar only", () => {
  assert.deepEqual(parseFlags("hide_sidebar=1"), {
    hideHeader: false,
    hideSidebar: true,
  });
});

test("parseFlags: empty search disables chrome", () => {
  assert.deepEqual(parseFlags(""), {
    hideHeader: false,
    hideSidebar: false,
  });
});

test("buildCss includes header and sidebar rules for kiosk", () => {
  const css = buildCss({ hideHeader: true, hideSidebar: true });
  assert.match(css, /header/);
  assert.match(css, /sidebar/);
});

test("applyKioskChrome injects and removes style tag", () => {
  const styles = new Map();
  const doc = {
    getElementById: (id) => styles.get(id) || null,
    createElement: (tag) => {
      const el = {
        tag,
        id: "",
        textContent: "",
        remove: () => styles.delete(el.id),
      };
      return el;
    },
    head: {
      appendChild: (el) => {
        styles.set(el.id, el);
      },
    },
  };

  assert.equal(applyKioskChrome({ hideHeader: true, hideSidebar: false }, doc), true);
  assert.equal(styles.has("kpanel-kiosk-style"), true);
  assert.match(styles.get("kpanel-kiosk-style").textContent, /header/);

  assert.equal(applyKioskChrome({ hideHeader: false, hideSidebar: false }, doc), false);
  assert.equal(styles.has("kpanel-kiosk-style"), false);
});
