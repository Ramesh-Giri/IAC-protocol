// Offline behavior checks; no DOM package or browser dependency.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function element(attributes = {}) {
  return {
    attributes, hidden: false, tabIndex: -1, focused: false, events: {},
    getAttribute(name) { return this.attributes[name]; },
    setAttribute(name, value) { this.attributes[name] = value; },
    addEventListener(name, handler) { this.events[name] = handler; },
    focus() { this.focused = true; },
  };
}
const tabs = [element({"aria-controls": "simple-panel"}), element({"aria-controls": "complex-panel"})];
const panels = {"simple-panel": element(), "complex-panel": element()};
const tablist = element();
tablist.hidden = true;
const classes = new Set();
const document = {
  querySelectorAll: selector => { assert.equal(selector, '[role="tab"]'); return tabs; },
  querySelector: selector => { assert.equal(selector, '[role="tablist"]'); return tablist; },
  getElementById: id => panels[id],
  body: {classList: {add: value => classes.add(value)}},
};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "switch.js"), "utf8"), {document});

function selected(index) {
  tabs.forEach((tab, position) => {
    assert.equal(tab.attributes["aria-selected"], String(position === index));
    assert.equal(tab.tabIndex, position === index ? 0 : -1);
    assert.equal(panels[tab.attributes["aria-controls"]].hidden, position !== index);
  });
}
function key(index, value) {
  let prevented = false;
  tabs[index].events.keydown({key: value, preventDefault() { prevented = true; }});
  return prevented;
}
selected(0);
assert.equal(tablist.hidden, false);
assert(classes.has("enhanced"));
tabs[1].events.click(); selected(1);
tabs[0].events.click(); selected(0);
assert(key(0, "ArrowRight")); selected(1); assert(tabs[1].focused);
assert(key(1, "ArrowRight")); selected(0);
assert(key(0, "ArrowLeft")); selected(1);
assert(key(1, "Home")); selected(0);
assert(key(0, "End")); selected(1);
assert.equal(key(1, "Tab"), false); selected(1);
console.log("Diagram switch: click, keyboard, focus and panel visibility checks passed.");
