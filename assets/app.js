/* =====================================================================
   Bizautosetup: app.js (final)
   Works with build.py markup and style-final.css.
   - Theme (dark default, remembered)
   - Mobile menu, back-to-top, scroll reveal, typing role text
   - Broken image fallback (any element with [data-fallback])
   - Gallery tabs, service filter and search, savings calculator
   - Lightbox and "all samples" modal (hidden attribute + .open class)
   - Forms to Google Sheet with honeypot, validation, timeout
   - Rule based chatbot
   ===================================================================== */
(() => {
  "use strict";

  /* ---------- helpers ---------- */
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const root = document.documentElement;
  const body = document.body;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // WhatsApp number is read from the floating WhatsApp link, so there is one source of truth
  const WA_HREF = $("#wa")?.getAttribute("href") || "";
  const WA_NUMBER = (WA_HREF.match(/wa\.me\/(\d+)/) || [])[1] || "";
  const waLink = text => (WA_NUMBER ? `https://wa.me/${WA_NUMBER}?text=${encodeURIComponent(text)}` : "#");
  const inr = n => "₹ " + Math.round(n).toLocaleString("en-IN");
  const absUrl = href => { try { return new URL(href, location.href).href; } catch (_) { return ""; } };
  const EMAIL = $("a[href^='mailto:']")?.textContent.trim() || "";
  const PHONE = $("a[href^='tel:']")?.textContent.trim() || "";

  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (_) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (_) { /* storage blocked: ignore */ } }
  };

  /* ---------- THEME ---------- */
  if (store.get("theme") === "light") root.dataset.theme = "light";
  const themeBtn = $("#themeBtn");
  const syncTheme = () => {
    if (themeBtn) themeBtn.textContent = root.dataset.theme === "dark" ? "Light mode" : "Dark mode";
  };
  themeBtn?.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
    store.set("theme", root.dataset.theme);
    syncTheme();
  });
  syncTheme();

  /* ---------- NAV, MOBILE MENU, BACK TO TOP ---------- */
  const nav = $("#nav"), links = $("#links"), burger = $("#burger"), topBtn = $("#top");

  const setMenu = open => {
    links?.classList.toggle("open", open);
    burger?.setAttribute("aria-expanded", String(open));
  };
  burger?.addEventListener("click", () => setMenu(!links.classList.contains("open")));
  $$("#links a").forEach(a => a.addEventListener("click", () => setMenu(false)));
  window.matchMedia("(min-width: 981px)").addEventListener("change", e => { if (e.matches) setMenu(false); });

  let scrollTicking = false;
  const onScroll = () => {
    if (scrollTicking) return;
    scrollTicking = true;
    requestAnimationFrame(() => {
      nav?.classList.toggle("scrolled", window.scrollY > 30);
      if (topBtn) topBtn.hidden = window.scrollY < 600;
      scrollTicking = false;
    });
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  topBtn?.addEventListener("click", e => {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
  });

  /* ---------- SCROLL REVEAL ---------- */
  const revealEls = $$(".rv");
  if ("IntersectionObserver" in window && !reduceMotion) {
    const io = new IntersectionObserver((entries, obs) => entries.forEach(en => {
      if (en.isIntersecting) {
        en.target.classList.add("in");
        obs.unobserve(en.target);
      }
    }), { threshold: 0.1 });
    revealEls.forEach(el => io.observe(el));
  } else {
    revealEls.forEach(el => el.classList.add("in"));
  }

  /* ---------- ROLE TEXT (typing effect) ---------- */
  const roleEl = $("#role");
  if (roleEl) {
    const roles = ["MIS Specialist", "Automation Expert", "Custom System Builder", "WhatsApp & API Integrator"];
    if (reduceMotion) {
      roleEl.textContent = roles[0];
    } else {
      let ri = 0, ci = 0, deleting = false;
      const type = () => {
        const word = roles[ri];
        roleEl.textContent = word.slice(0, ci);
        if (!deleting && ci < word.length) { ci++; return setTimeout(type, 80); }
        if (deleting && ci > 0) { ci--; return setTimeout(type, 40); }
        deleting = !deleting;
        if (!deleting) ri = (ri + 1) % roles.length;
        setTimeout(type, deleting ? 1500 : 300);
      };
      type();
    }
  }

  /* ---------- BROKEN IMAGE FALLBACK ----------
     Any <img> inside [data-fallback] gets class "missing" when it fails.
     CSS then hides the image and shows the placeholder text. */
  document.addEventListener("error", e => {
    const img = e.target;
    if (!(img instanceof HTMLImageElement)) return;
    img.closest("[data-fallback]")?.classList.add("missing");
  }, true);
  // images that failed before this script ran (eager images only, lazy ones fire their own error)
  $$("img:not([loading='lazy'])").forEach(img => {
    if (img.complete && img.naturalWidth === 0 && img.getAttribute("src")) {
      img.closest("[data-fallback]")?.classList.add("missing");
    }
  });

  /* ---------- GALLERY (homepage tabs) ---------- */
  const showcase = $("#showcase");
  if (showcase) {
    const tabs = $$(".g-tab", showcase);
    const slides = $$(".g-slide", showcase);
    const descs = $$(".g-desc", showcase);

    const selectSlide = i => {
      tabs.forEach((t, n) => {
        t.classList.toggle("on", n === i);
        t.setAttribute("aria-selected", String(n === i));
        t.tabIndex = n === i ? 0 : -1;
      });
      slides.forEach((s, n) => s.classList.toggle("on", n === i));
      descs.forEach((d, n) => d.classList.toggle("on", n === i));
    };

    tabs.forEach((t, i) => {
      t.addEventListener("click", () => selectSlide(i));
      t.addEventListener("keydown", e => {
        if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
        const next = (i + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
        tabs[next].focus();
        selectSlide(next);
      });
    });
    selectSlide(Math.max(0, tabs.findIndex(t => t.classList.contains("on"))));
  }

  /* ---------- SERVICE FILTER + SEARCH (homepage) ---------- */
  const svcGrid = $("#svcGrid");
  if (svcGrid) {
    const cards = $$(".card", svcGrid);
    const chips = $$("#chips .chip");
    const countEl = $("#count"), emptyEl = $("#empty"), search = $("#q");
    let cat = "all", q = "";

    const apply = () => {
      let shown = 0;
      cards.forEach(c => {
        const okCat = cat === "all" || c.dataset.cat === cat;
        const okQ = !q || (c.dataset.search || "").includes(q);
        const ok = okCat && okQ;
        c.hidden = !ok;
        if (ok) shown++;
      });
      if (emptyEl) emptyEl.hidden = shown > 0;
      if (countEl) countEl.textContent = `Showing ${shown} of ${cards.length} systems`;
    };

    chips.forEach(ch => ch.addEventListener("click", () => {
      cat = ch.dataset.cat || "all";
      chips.forEach(x => {
        x.classList.toggle("on", x === ch);
        x.setAttribute("aria-pressed", String(x === ch));
      });
      apply();
    }));
    search?.addEventListener("input", () => {
      q = search.value.trim().toLowerCase();
      apply();
    });
    apply();
  }

  /* ---------- SAVINGS CALCULATOR ---------- */
  const calc = $("#calc");
  if (calc) {
    const num = id => {
      const v = parseFloat($("#" + id)?.value);
      return Number.isFinite(v) ? Math.max(0, v) : 0;
    };
    const run = () => {
      const pct = Math.min(100, num("cPct")) / 100;
      const days = num("cDays");
      const hoursMonth = num("cStaff") * num("cHours") * days * pct;
      const hourly = days > 0 ? num("cSalary") / (days * 8) : 0;
      const monthly = hoursMonth * hourly;
      $("#rHours").textContent = Math.round(hoursMonth).toLocaleString("en-IN") + " hrs";
      $("#rMonth").textContent = inr(monthly);
      $("#rYear").textContent = inr(monthly * 12);
    };
    calc.addEventListener("input", run);
    run();
  }

  /* ---------- LIGHTBOX + ALL SAMPLES MODAL (service pages) ---------- */
  const lb = $("#lb"), lbImg = $("#lbImg"), lbCap = $("#lbCap"), lbCount = $("#lbCount");
  const lbStage = $("#lbStage"), lbZoom = $("#lbZoom"), lbClose = $("#lbClose");
  const lbPrev = $("#lbPrev"), lbNext = $("#lbNext");
  const gm = $("#gm"), gmGrid = $("#gmGrid"), gmTitle = $("#gmTitle"), gmSub = $("#gmSub");
  const galEl = $("#gal-data");

  let GAL = [];
  try { GAL = galEl ? JSON.parse(galEl.textContent) : []; } catch (_) { GAL = []; }

  let cur = 0;
  let lastFocus = null;

  const lockPage = () => body.classList.add("lock");
  const unlockPage = () => {
    if ((!lb || lb.hidden) && (!gm || gm.hidden)) body.classList.remove("lock");
  };
  const rememberFocus = () => { lastFocus = document.activeElement; };
  const restoreFocus = () => {
    if (lastFocus && typeof lastFocus.focus === "function") lastFocus.focus({ preventScroll: true });
    lastFocus = null;
  };

  if (lbImg) lbImg.addEventListener("error", () => { lbCap.textContent = "Image not found"; });

  const showLB = () => {
    const it = GAL[cur];
    if (!it || !lbImg) return;
    lbStage.classList.remove("zoomed");
    lbZoom.textContent = "Zoom";
    lbImg.src = it.src;
    lbImg.alt = it.alt;
    lbCap.textContent = it.alt;
    lbCount.textContent = `${cur + 1} / ${GAL.length}`;
    const multi = GAL.length > 1;
    lbPrev.hidden = !multi;
    lbNext.hidden = !multi;
  };

  const openLB = i => {
    if (!lb || !GAL.length) return;
    rememberFocus();
    cur = Math.min(Math.max(0, i), GAL.length - 1);
    showLB();
    lb.hidden = false;
    lockPage();
    lbClose?.focus({ preventScroll: true });
  };

  const closeLB = () => {
    if (!lb) return;
    lb.hidden = true;
    lbImg.removeAttribute("src");
    unlockPage();
    restoreFocus();
  };

  const step = d => {
    if (GAL.length < 2) return;
    cur = (cur + d + GAL.length) % GAL.length;
    showLB();
  };

  const toggleZoom = () => {
    const zoomed = lbStage.classList.toggle("zoomed");
    lbZoom.textContent = zoomed ? "Fit" : "Zoom";
    lbStage.scrollTo(0, 0);
  };

  lbClose?.addEventListener("click", closeLB);
  lbPrev?.addEventListener("click", () => step(-1));
  lbNext?.addEventListener("click", () => step(1));
  lbZoom?.addEventListener("click", toggleZoom);
  lbImg?.addEventListener("click", toggleZoom);
  lbStage?.addEventListener("click", e => { if (e.target === lbStage) closeLB(); });

  // swipe left / right on phones (not while zoomed)
  let touchX = null;
  lb?.addEventListener("touchstart", e => { touchX = e.touches[0].clientX; }, { passive: true });
  lb?.addEventListener("touchend", e => {
    if (touchX === null || lbStage.classList.contains("zoomed")) { touchX = null; return; }
    const dx = e.changedTouches[0].clientX - touchX;
    touchX = null;
    if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
  });

  const openGM = () => {
    if (!gm) return;
    rememberFocus();
    gm.hidden = false;
    lockPage();
    gm.querySelector("[data-close]")?.focus({ preventScroll: true });
  };
  const closeGM = () => {
    if (!gm) return;
    gm.hidden = true;
    unlockPage();
    restoreFocus();
  };
  gm?.addEventListener("click", e => {
    if (e.target === gm || e.target.closest("[data-close]")) closeGM();
  });

  // single thumbnail opens the lightbox at that image
  $$("[data-open]").forEach(btn => {
    btn.addEventListener("click", () => openLB(Number(btn.dataset.open) || 0));
  });

  // "View all" builds the grid inside the modal, then opens it
  $$("[data-all]").forEach(btn => {
    btn.addEventListener("click", () => {
      if (!GAL.length || !gm) return;
      gmTitle.textContent = "Sample screens";
      gmSub.textContent = `${GAL.length} sample screens`;
      gmGrid.textContent = "";
      GAL.forEach((it, i) => {
        const t = document.createElement("button");
        t.type = "button";
        t.className = "thumb";
        t.setAttribute("aria-label", it.alt);
        t.setAttribute("data-fallback", "");
        const img = document.createElement("img");
        img.src = it.src;
        img.alt = it.alt;
        img.loading = "lazy";
        img.decoding = "async";
        const miss = document.createElement("span");
        miss.className = "thumb-missing";
        miss.textContent = "Screen not available";
        t.append(img, miss);
        t.addEventListener("click", () => { closeGM(); openLB(i); });
        gmGrid.append(t);
      });
      openGM();
    });
  });

  /* ---------- CHATBOT ---------- */
  const bot = $("#bot"), botBtn = $("#botBtn"), botClose = $("#botClose");
  const botLog = $("#botLog"), botOpts = $("#botOpts");
  const botApi = { isOpen: () => false, close: () => {} };

  if (bot && botBtn && botLog && botOpts) {
    const inService = location.pathname.includes("/services/");
    const homeUrl = inService ? "../index.html" : "index.html";
    const servicesUrl = homeUrl + "#services";
    const contactUrl = homeUrl + "#contact";
    const waMsg = "Hello, I have a question about an automation project.";

    // services list from the cards on this page (absolute URLs, de-duplicated)
    const seen = new Map();
    $$(".card[href]").forEach(c => {
      const href = absUrl(c.getAttribute("href"));
      const name = ($("h3", c)?.textContent || "").trim();
      if (!href || !name || seen.has(href)) return;
      seen.set(href, { name, href, ico: ($(".ico", c)?.textContent || "").trim() });
    });
    const SERVICES = Array.from(seen.values());

    const TOPICS = [
      { key: "services", label: "What services do you offer?" },
      { key: "price", label: "What is the price?" },
      { key: "demo", label: "Can I see a demo?" },
      { key: "time", label: "How long does it take?" },
      { key: "docs", label: "What do you need from me?" },
      { key: "support", label: "Do you provide support?" },
      { key: "about", label: "Who are you?" },
      { key: "contact", label: "How can I contact you?" }
    ];

    const ANSWERS = {
      price: "Pricing depends on your process, so every system is quotation based.\n\nChoose the system you need and submit the quotation form. I will review your requirement and send a quotation.",
      demo: "Each system has its own page with sample screens. Open any system from the Services section to see them.",
      time: "The timeline depends on your requirement. Small systems can be ready in a few days, and larger systems are delivered in milestones. I share the exact timeline with your quotation.",
      docs: "You only need to explain your process: who does the work, which registers or files you use, and what problem you face. I handle the setup.",
      support: "Yes. I provide training, documentation and support after go-live, including fixes and upgrades.",
      about: "I am Amit, an MIS & Automation Specialist with 6 years of hands-on experience. I build systems on Google Sheets, Apps Script, WhatsApp and APIs.",
      contact: `You can reach me here:\n• Email: ${EMAIL}\n• WhatsApp / Mobile: ${PHONE}\n\nOr submit the contact form and I will reply soon.`
    };

    const addMsg = (text, who) => {
      const d = document.createElement("div");
      d.className = "msg " + (who === "user" ? "user-msg" : "bot-msg");
      d.textContent = text;
      botLog.append(d);
      botLog.scrollTop = botLog.scrollHeight;
    };

    const addLink = (text, href) => {
      const d = document.createElement("div");
      d.className = "msg bot-msg";
      const a = document.createElement("a");
      a.href = href;
      a.textContent = text;
      if (/^https?:/.test(href)) {
        a.target = "_blank";
        a.rel = "noopener noreferrer";
      }
      d.append(a);
      botLog.append(d);
      botLog.scrollTop = botLog.scrollHeight;
    };

    const setOpts = list => {
      botOpts.textContent = "";
      list.forEach(o => {
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = o.label;
        b.addEventListener("click", o.run);
        botOpts.append(b);
      });
    };

    const mainMenu = () => setOpts(TOPICS.map(t => ({ label: t.label, run: () => answer(t.key) })));

    const serviceMenu = () => {
      setOpts([
        ...SERVICES.map(s => ({
          label: `${s.ico} ${s.name}`.trim(),
          run: () => {
            addMsg(`${s.ico} ${s.name}`.trim(), "user");
            addMsg("Details, sample screens and the quotation form are on that system's page.", "bot");
            addLink("Open details →", s.href);
            addMsg("Anything else you would like to know?", "bot");
            mainMenu();
          }
        })),
        { label: "← Back", run: mainMenu }
      ]);
    };

    const answer = key => {
      const label = TOPICS.find(t => t.key === key)?.label || "";
      addMsg(label, "user");

      if (key === "services") {
        if (!SERVICES.length) {
          addMsg("You can see all systems in the Services section.", "bot");
          addLink("View services →", servicesUrl);
          mainMenu();
          return;
        }
        addMsg("I build these systems:\n" + SERVICES.map(s => "• " + s.name).join("\n") + "\n\nWhich one would you like to know about?", "bot");
        serviceMenu();
        return;
      }

      addMsg(ANSWERS[key], "bot");
      if (key === "demo") addLink("View services →", servicesUrl);
      if (key === "price") addLink("Open a system and request a quotation →", servicesUrl);
      if (key === "contact") {
        addLink("Submit the contact form →", contactUrl);
        addLink("Message on WhatsApp →", waLink(waMsg));
      }
      addMsg("Anything else you would like to know?", "bot");
      mainMenu();
    };

    function openBot() {
      bot.hidden = false;
      botBtn.setAttribute("aria-expanded", "true");
      if (!botLog.childElementCount) {
        addMsg("Hello! I am the Bizautosetup assistant. What would you like to know?", "bot");
        mainMenu();
      }
      botClose?.focus({ preventScroll: true });
    }

    function closeBot() {
      bot.hidden = true;
      botBtn.setAttribute("aria-expanded", "false");
      botBtn.focus({ preventScroll: true });
    }

    botBtn.addEventListener("click", () => (bot.hidden ? openBot() : closeBot()));
    botClose?.addEventListener("click", closeBot);
    botApi.isOpen = () => !bot.hidden;
    botApi.close = closeBot;
  }

  /* ---------- FORMS -> GOOGLE SHEET ---------- */
  const download = href => {
    const a = document.createElement("a");
    a.href = href;
    a.download = href.split("/").pop();
    document.body.append(a);
    a.click();
    a.remove();
  };

  $$("form.lead").forEach(form => {
    const notice = $(".notice", form);
    const nl = $(".nl", form);
    const btn = $('button[type="submit"]', form);
    const label = btn ? btn.textContent : "Send";

    const showNotice = (ok, title, text, waText) => {
      if (!notice) return;
      notice.hidden = false;
      notice.classList.toggle("error", !ok);
      $(".ni", notice).textContent = ok ? "✓" : "!";
      $(".nt", notice).textContent = title;
      $(".np", notice).textContent = text;
      if (nl) {
        nl.hidden = !waText;
        if (waText) nl.href = waLink(waText);
      }
      notice.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "nearest" });
      clearTimeout(notice._t);
      notice._t = setTimeout(() => { notice.hidden = true; }, 12000);
    };

    form.addEventListener("submit", async e => {
      e.preventDefault();
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }

      const fd = new FormData(form);
      if (fd.get("website")) return; // honeypot: only bots fill this hidden field

      const data = {};
      for (const [k, v] of fd.entries()) {
        if (k !== "website") data[k] = String(v).trim();
      }

      const endpoint = form.dataset.endpoint || "";
      if (!/^https:\/\/script\.google\.com\//.test(endpoint)) {
        showNotice(false, "Form not configured",
          "Please contact me directly on WhatsApp.",
          "Hello, I need help with: " + (data.service || "automation"));
        return;
      }

      if (btn) { btn.disabled = true; btn.textContent = "Sending..."; }
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 15000);

      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "text/plain;charset=utf-8" }, // simple request: no CORS preflight
          body: JSON.stringify({
            ...data,
            type: form.dataset.type || "Contact",
            page: location.href,
            time: new Date().toISOString()
          }),
          signal: ctrl.signal
        });

        const text = await res.text();
        let out = null;
        try { out = JSON.parse(text); } catch (_) { out = null; }
        if (!out || out.ok !== true) {
          throw new Error(out?.error || "Could not save your request. Please try again.");
        }

        const pdf = form.dataset.pdf;
        form.reset();
        if (pdf) {
          showNotice(true, "Thank you!", "Your quotation is downloading. I will also contact you shortly.");
          download(pdf);
        } else {
          showNotice(true, "Thank you!", "Your request is received. I will contact you shortly.");
        }
      } catch (err) {
        console.error("Form error:", err);
        const msg = err.name === "AbortError"
          ? "The server took too long. Please try again."
          : (err.message || "Please try again, or message me on WhatsApp.");
        showNotice(false, "Could not send right now", msg,
          "Hello, I need help with: " + (data.service || "automation"));
      } finally {
        clearTimeout(timer);
        if (btn) { btn.disabled = false; btn.textContent = label; }
      }
    });
  });

  /* ---------- ONE KEYBOARD HANDLER ---------- */
  document.addEventListener("keydown", e => {
    if (lb && !lb.hidden) {
      if (e.key === "Escape") closeLB();
      else if (e.key === "ArrowRight") step(1);
      else if (e.key === "ArrowLeft") step(-1);
      else if (e.key === "z" || e.key === "Z") toggleZoom();
      return;
    }
    if (gm && !gm.hidden && e.key === "Escape") { closeGM(); return; }
    if (botApi.isOpen() && e.key === "Escape") { botApi.close(); return; }
    if (links?.classList.contains("open") && e.key === "Escape") setMenu(false);
  });
})();