(function(){
  "use strict";
  var SNAP = %SNAP%;              // snapshot epoch (seconds)
  var FRESH = %FRESH%, AGING = %AGING%;

  function dur(s, short){
    if (s === null || s === undefined || isNaN(s)) return "unknown";
    var neg = s < 0; s = Math.abs(Math.floor(s)); var o;
    if (s < 60) o = s + "s";
    else if (s < 3600) o = Math.floor(s/60) + "m";
    else if (s < 86400) o = Math.floor(s/3600) + "h " + Math.floor((s%3600)/60) + "m";
    else o = Math.floor(s/86400) + "d " + Math.floor((s%86400)/3600) + "h";
    return (neg ? "-" : "") + o;
  }
  var ages = [].slice.call(document.querySelectorAll(".age[data-epoch]"));
  var vols = [].slice.call(document.querySelectorAll(".v[data-fc='volatile']"));
  var monos = [].slice.call(document.querySelectorAll(".m[data-fc='monotone']"));
  vols.forEach(function(el){ el.dataset.orig = el.innerHTML; });
  monos.forEach(function(el){ el.dataset.orig = el.textContent; });

  function tick(){
    var now = Math.floor(Date.now()/1000);
    var pageAge = now - SNAP;

    ages.forEach(function(el){
      var ep = parseInt(el.dataset.epoch, 10);
      el.textContent = dur(Math.max(0, now - ep), true) + (el.dataset.suffix || "");
    });

    // header
    var hdr = document.getElementById("snapage");
    if (hdr) hdr.textContent = dur(pageAge, true) + " ago";
    var word = pageAge < FRESH ? "FRESH" : (pageAge < AGING ? "AGING" : "STALE");
    var w = document.getElementById("staleword");
    if (w && w.textContent !== word){
      w.textContent = word;
      w.className = "stale-word stale-" + word;
    }
    var banner = document.getElementById("decaybanner");
    if (banner){
      banner.textContent = pageAge < FRESH
        ? "volatile fields at full strength"
        : (pageAge < AGING
           ? "volatile fields are dimmed — they were true " + dur(pageAge,true) + " ago and are no longer asserted at full strength"
           : "volatile fields have expired: liveness, dirty-tree and ahead/behind now read UNKNOWN. Re-run the generator.");
      banner.className = "note " + (pageAge < FRESH ? "" : (pageAge < AGING ? "t-warn" : "t-bad"));
    }

    // volatile decay
    var stale = pageAge >= AGING, degraded = pageAge >= FRESH && !stale;
    vols.forEach(function(el){
      if (stale){
        if (el.dataset.stale !== "1"){
          el.dataset.stale = "1";
          el.innerHTML = el.dataset.unknown || "&mdash;";
          el.title = "volatile field, last observed " + dur(pageAge,true) + " ago — no longer asserted";
        }
      } else {
        if (el.dataset.stale === "1"){ el.innerHTML = el.dataset.orig; delete el.dataset.stale; }
        if (degraded) el.dataset.degraded = "1"; else delete el.dataset.degraded;
      }
    });

    // monotone: only ever grows while this page sits open
    monos.forEach(function(el){
      var o = el.dataset.orig || "";
      el.textContent = (pageAge >= FRESH ? "at least " : "") + o;
    });
  }
  tick();
  setInterval(tick, 1000);

  // ---- matrix -> river filter (view only; this page cannot act) ----------
  var chip = document.getElementById("filterchip");
  var rows = [].slice.call(document.querySelectorAll("#river tbody tr"));
  var cells = [].slice.call(document.querySelectorAll(".matrix .cell"));
  function applyFilter(f, t){
    cells.forEach(function(c){
      c.setAttribute("aria-pressed", String(!!f && c.dataset.f === f && c.dataset.t === t));
    });
    rows.forEach(function(r){
      r.hidden = !!f && !(r.dataset.f === f && r.dataset.t === t);
    });
    if (chip){
      if (f){
        chip.hidden = false;
        chip.firstElementChild.textContent = "showing " + f + " → " + t;
        var d = document.getElementById("riverwrap");
        if (d && !d.open) d.open = true;
      } else { chip.hidden = true; }
    }
  }
  cells.forEach(function(c){
    function go(){
      var on = c.getAttribute("aria-pressed") === "true";
      if (on) applyFilter(null, null); else applyFilter(c.dataset.f, c.dataset.t);
    }
    c.addEventListener("click", go);
    c.addEventListener("keydown", function(ev){
      if (ev.key === "Enter" || ev.key === " "){ ev.preventDefault(); go(); }
    });
  });
  var clr = document.getElementById("clearfilter");
  if (clr) clr.addEventListener("click", function(){ applyFilter(null, null); });

  // ---- sortable triage table (view only; buckets stay grouped) -----------
  var triage = document.getElementById("triage");
  if (triage){
    var tb = triage.tBodies[0];
    var groups = [];   // [{header, rows}] preserved so buckets never interleave
    var cur = null;
    [].slice.call(tb.rows).forEach(function(r){
      if (r.classList.contains("bucket")){ cur = {header:r, rows:[]}; groups.push(cur); }
      else if (cur) cur.rows.push(r);
      else groups.push({header:null, rows:[r]});
    });
    [].slice.call(triage.querySelectorAll("th[data-sort]")).forEach(function(th){
      function sort(){
        var key = th.dataset.sort;
        var dir = th.getAttribute("aria-sort") === "descending" ? 1 : -1;
        [].slice.call(triage.querySelectorAll("th[data-sort]")).forEach(function(o){
          o.removeAttribute("aria-sort");
        });
        th.setAttribute("aria-sort", dir === -1 ? "descending" : "ascending");
        groups.forEach(function(g){
          g.rows.sort(function(a,b){
            var av = parseFloat(a.dataset[key] || "0"), bv = parseFloat(b.dataset[key] || "0");
            if (isNaN(av)) av = 0; if (isNaN(bv)) bv = 0;
            return (av - bv) * dir;
          });
          g.rows.forEach(function(r){ tb.appendChild(r); });
        });
        // re-append headers in their original order, each before its rows
        groups.forEach(function(g){
          if (g.header) tb.insertBefore(g.header, g.rows[0] || null);
        });
      }
      th.addEventListener("click", sort);
      th.addEventListener("keydown", function(ev){
        if (ev.key === "Enter" || ev.key === " "){ ev.preventDefault(); sort(); }
      });
    });
  }

  // ---- layout: collapse + reorder, remembered per browser ----------------
  // View state only. Nothing here can act on the network, and no arrangement
  // changes a single thing the page asserts.
  var LS_ORDER = "netdash-order", LS_SHUT = "netdash-collapsed";
  var main = document.querySelector("main");

  function panels(){ return [].slice.call(main.querySelectorAll("section.panel")); }
  function store(k, v){ try { localStorage.setItem(k, JSON.stringify(v)); } catch(e){} }
  function load(k){
    try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : null; } catch(e){ return null; }
  }
  function saveOrder(){ store(LS_ORDER, panels().map(function(p){ return p.dataset.pid; })); }
  function saveShut(){
    store(LS_SHUT, panels().filter(function(p){ return p.hasAttribute("data-collapsed"); })
                           .map(function(p){ return p.dataset.pid; }));
  }
  function setOpen(p, open){
    if (open) p.removeAttribute("data-collapsed"); else p.setAttribute("data-collapsed", "1");
    var b = p.querySelector(".ph-btn");
    if (b) b.setAttribute("aria-expanded", String(!!open));
  }

  // restore a remembered arrangement; unknown or missing panels keep their
  // generated position rather than disappearing
  var savedOrder = load(LS_ORDER);
  if (savedOrder && savedOrder.length){
    var byId = {};
    panels().forEach(function(p){ byId[p.dataset.pid] = p; });
    savedOrder.forEach(function(pid){ if (byId[pid]) main.appendChild(byId[pid]); });
    panels().forEach(function(p){ if (savedOrder.indexOf(p.dataset.pid) === -1) main.appendChild(p); });
  }
  var savedShut = load(LS_SHUT);
  if (savedShut){
    panels().forEach(function(p){ setOpen(p, savedShut.indexOf(p.dataset.pid) === -1); });
  }

  panels().forEach(function(p){
    var btn = p.querySelector(".ph-btn");
    if (btn) btn.addEventListener("click", function(){
      setOpen(p, p.hasAttribute("data-collapsed"));
      saveShut();
    });
  });

  var eAll = document.getElementById("expandall"), cAll = document.getElementById("collapseall"),
      reset = document.getElementById("resetlayout");
  if (eAll) eAll.addEventListener("click", function(){
    panels().forEach(function(p){ setOpen(p, true); }); saveShut();
  });
  if (cAll) cAll.addEventListener("click", function(){
    panels().forEach(function(p){ setOpen(p, false); }); saveShut();
  });
  if (reset) reset.addEventListener("click", function(){
    try { localStorage.removeItem(LS_ORDER); localStorage.removeItem(LS_SHUT); } catch(e){}
    location.reload();
  });

  // drag to reorder, from the handle only so text stays selectable
  var dragged = null;
  function clearMarks(){
    panels().forEach(function(p){ p.classList.remove("drop-before", "drop-after", "dragging"); });
  }
  panels().forEach(function(p){
    var handle = p.querySelector(".drag");
    if (!handle) return;
    handle.addEventListener("dragstart", function(ev){
      dragged = p;
      p.classList.add("dragging");
      try {
        ev.dataTransfer.effectAllowed = "move";
        ev.dataTransfer.setData("text/plain", p.dataset.pid);
        ev.dataTransfer.setDragImage(p, 20, 12);
      } catch(e){}
    });
    handle.addEventListener("dragend", function(){ clearMarks(); dragged = null; saveOrder(); });
    p.addEventListener("dragover", function(ev){
      if (!dragged || dragged === p) return;
      ev.preventDefault();
      var r = p.getBoundingClientRect();
      var before = (ev.clientY - r.top) < r.height / 2;
      p.classList.toggle("drop-before", before);
      p.classList.toggle("drop-after", !before);
    });
    p.addEventListener("dragleave", function(){
      p.classList.remove("drop-before", "drop-after");
    });
    p.addEventListener("drop", function(ev){
      if (!dragged || dragged === p) return;
      ev.preventDefault();
      var r = p.getBoundingClientRect();
      var before = (ev.clientY - r.top) < r.height / 2;
      main.insertBefore(dragged, before ? p : p.nextSibling);
      clearMarks();
      saveOrder();
    });
    // keyboard equivalent: the handle is focusable, alt+arrows move the panel
    handle.addEventListener("keydown", function(ev){
      if (ev.key === "Enter" || ev.key === " "){
        ev.preventDefault();
        setOpen(p, p.hasAttribute("data-collapsed"));
        saveShut();
        return;
      }
      if (!ev.altKey || (ev.key !== "ArrowUp" && ev.key !== "ArrowDown")) return;
      ev.preventDefault();
      if (ev.key === "ArrowUp" && p.previousElementSibling) main.insertBefore(p, p.previousElementSibling);
      if (ev.key === "ArrowDown" && p.nextElementSibling) main.insertBefore(p.nextElementSibling, p);
      handle.focus();
      p.classList.add("flash");
      setTimeout(function(){ p.classList.remove("flash"); }, 600);
      saveOrder();
    });
  });

  // a link to a shut panel opens it, otherwise the anchor lands on nothing
  function revealFromHash(){
    var id = (location.hash || "").replace("#", "");
    if (!id) return;
    var p = document.getElementById(id);
    if (p && p.classList.contains("panel")){
      setOpen(p, true);
      saveShut();
      p.scrollIntoView({block: "start"});
    }
  }
  window.addEventListener("hashchange", revealFromHash);
  [].slice.call(document.querySelectorAll('a[href^="#p"]')).forEach(function(a){
    a.addEventListener("click", function(){ setTimeout(revealFromHash, 0); });
  });
  revealFromHash();

  // ---- theme (view only) -------------------------------------------------
  var btns = [].slice.call(document.querySelectorAll(".themectl button"));
  function setTheme(mode){
    if (mode === "auto") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", mode);
    btns.forEach(function(b){ b.setAttribute("aria-pressed", String(b.dataset.theme === mode)); });
    try { localStorage.setItem("agentmail-dash-theme", mode); } catch(e){}
  }
  btns.forEach(function(b){ b.addEventListener("click", function(){ setTheme(b.dataset.theme); }); });
  var saved = null;
  try { saved = localStorage.getItem("agentmail-dash-theme"); } catch(e){}
  setTheme(saved || "auto");
})();
