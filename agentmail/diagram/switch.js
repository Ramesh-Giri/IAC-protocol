"use strict";

const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
const panels = tabs.map(tab => document.getElementById(tab.getAttribute("aria-controls")));

function selectView(index, moveFocus = false) {
  tabs.forEach((tab, position) => {
    const selected = position === index;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    panels[position].hidden = !selected;
  });
  if (moveFocus) tabs[index].focus();
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectView(index));
  tab.addEventListener("keydown", event => {
    const destinations = {
      ArrowRight: (index + 1) % tabs.length,
      ArrowLeft: (index + tabs.length - 1) % tabs.length,
      Home: 0,
      End: tabs.length - 1,
    };
    if (!Object.prototype.hasOwnProperty.call(destinations, event.key)) return;
    event.preventDefault();
    selectView(destinations[event.key], true);
  });
});

selectView(0);
document.body.classList.add("enhanced");
document.querySelector('[role="tablist"]').hidden = false;
