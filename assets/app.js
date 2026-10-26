(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const root = document.documentElement;
  const body = document.body;
  const WA = body.dataset.wa || "";
  const inr = n => "₹ " + Math.round(n).toLocaleString("en-IN");
  const waLink = t => `https://wa.me/${WA}?text=${encodeURIComponent(t)}`;
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* storage blocked */ } }
  };

  /* ---------- THEME: dark by default, choice remembered ---------- */
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
  const nav = $("#nav"), topBtn = $("#top"), links = $("#links"), burger = $("#burger");
  const onScroll = () => {
    nav?.classList.toggle("scrolled", scrollY > 30);
    if (topBtn) topBtn.hidden = scrollY < 600;
  };
  addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  burger?.addEventListener("click", () => {
    const open = links.classList.toggle("open");
    burger.setAttribute("aria-expanded", open);
  });
  $$("#links a").forEach(a => a.addEventListener("click", () => {
    links.classList.remove("open");
    burger?.setAttribute("aria-expanded", "false");
  }));

  /* ---------- REVEAL ON SCROLL ---------- */
  const io = "IntersectionObserver" in window
    ? new IntersectionObserver(entries => entries.forEach(en => {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      }), { threshold: 0.1 })
    : null;
  $$(".rv").forEach(el => (io ? io.observe(el) : el.classList.add("in")));

  /* ---------- ROLE TYPING (homepage) ---------- */
  const roleEl = $("#role");
  if (roleEl) {
    const roles = ["MIS Specialist", "Automation Expert", "Custom System Builder", "WhatsApp & API Integrator"];
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
      roleEl.textContent = roles[0];
    } else {
      let ri = 0, ci = 0, del = false;
      (function type() {
        const word = roles[ri];
        roleEl.textContent = word.slice(0, ci);
        if (!del && ci < word.length) { ci++; return setTimeout(type, 80); }
        if (del && ci > 0) { ci--; return setTimeout(type, 40); }
        del = !del;
        if (!del) ri = (ri + 1) % roles.length;
        setTimeout(type, del ? 1500 : 300);
      })();
    }
  }

  /* ---------- PHOTO FALLBACK ---------- */
  const photo = $("#myPhoto");
  if (photo) {
    const fail = () => { photo.hidden = true; $("#photoFallback").hidden = false; };
    photo.addEventListener("error", fail);
    if (photo.complete && !photo.naturalWidth) fail();
  }

  /* ---------- GALLERY: one frame, tabs switch image ---------- */
  const showcase = $("#showcase");
  if (showcase) {
    const tabs = $$(".g-tab", showcase);
    const slides = $$(".g-slide", showcase);
    const descs = $$(".g-desc", showcase);
    const show = i => {
      tabs.forEach((t, n) => {
        t.classList.toggle("on", n === i);
        t.setAttribute("aria-selected", String(n === i));
      });
      slides.forEach((s, n) => s.classList.toggle("on", n === i));
      descs.forEach((d, n) => d.classList.toggle("on", n === i));
    };
    tabs.forEach((t, i) => t.addEventListener("click", () => show(i)));
    tabs.forEach((t, i) => t.addEventListener("keydown", e => {
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        const next = (i + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
        tabs[next].focus();
        show(next);
      }
    }));
  }

  /* ---------- SERVICE FILTER + SEARCH (homepage) ---------- */
  if ($("#svcGrid")) {
    const cards = $$("#svcGrid .card");
    const chips = $$("#chips .chip");
    const countEl = $("#count"), emptyEl = $("#empty"), search = $("#q");
    let cat = "all", q = "";
    const apply = () => {
      let n = 0;
      cards.forEach(c => {
        const ok = (cat === "all" || c.dataset.cat === cat) && (!q || c.dataset.search.includes(q));
        c.hidden = !ok;
        if (ok) n++;
      });
      emptyEl.hidden = n > 0;
      countEl.textContent = `Showing ${n} of ${cards.length} systems`;
    };
    chips.forEach(ch => ch.addEventListener("click", () => {
      cat = ch.dataset.cat;
      chips.forEach(x => x.classList.toggle("on", x === ch));
      apply();
    }));
    search?.addEventListener("input", () => { q = search.value.trim().toLowerCase(); apply(); });
    apply();
  }

  /* ---------- SAVINGS CALCULATOR ---------- */
  const calc = $("#calc");
  if (calc) {
    const num = id => Number($("#" + id).value) || 0;
    const run = () => {
      const pct = Math.min(100, Math.max(0, num("cPct"))) / 100;
      const days = num("cDays");
      const hoursM = num("cStaff") * num("cHours") * days * pct;
      const hourly = days > 0 ? num("cSalary") / (days * 8) : 0;
      const monthly = hoursM * hourly;
      $("#rHours").textContent = Math.round(hoursM).toLocaleString("en-IN") + " hrs";
      $("#rMonth").textContent = inr(monthly);
      $("#rYear").textContent = inr(monthly * 12);
    };
    calc.addEventListener("input", run);
    run();
  }

  /* ---------- LIGHTBOX + ALL-SAMPLES MODAL (service pages) ---------- */
  const galEl = $("#gal-data");
  const GAL = galEl ? JSON.parse(galEl.textContent) : [];
  const lb = $("#lb"), lbImg = $("#lbImg"), lbCap = $("#lbCap"), lbCount = $("#lbCount");
  const lbStage = $("#lbStage"), lbZoom = $("#lbZoom");
  const gm = $("#gm"), gmGrid = $("#gmGrid");
  let cur = 0;

  const lock = () => body.classList.add("lock");
  const unlock = () => {
    if (!document.querySelector(".modal.open") && !lb?.classList.contains("open")) body.classList.remove("lock");
  };

  const showLB = () => {
    const it = GAL[cur];
    lbStage.classList.remove("zoomed");
    lbZoom.textContent = "Zoom";
    lbImg.hidden = false;
    lbImg.src = it.src;
    lbImg.alt = it.alt;
    lbCap.textContent = it.alt;
    lbCount.textContent = `${cur + 1} / ${GAL.length}`;
    $("#lbPrev").hidden = GAL.length < 2;
    $("#lbNext").hidden = GAL.length < 2;
  };
  const openLB = i => { cur = i; showLB(); lb.classList.add("open"); lock(); };
  const closeLB = () => { lb.classList.remove("open"); lbImg.removeAttribute("src"); unlock(); };
  const step = d => { cur = (cur + d + GAL.length) % GAL.length; showLB(); };
  const toggleZoom = () => {
    const z = lbStage.classList.toggle("zoomed");
    lbZoom.textContent = z ? "Fit" : "Zoom";
    lbStage.scrollTo(0, 0);
  };
  lbImg?.addEventListener("error", () => { lbCap.textContent = "Image not found"; });

  $("#lbClose")?.addEventListener("click", closeLB);
  $("#lbPrev")?.addEventListener("click", () => step(-1));
  $("#lbNext")?.addEventListener("click", () => step(1));
  lbZoom?.addEventListener("click", toggleZoom);
  lbImg?.addEventListener("click", toggleZoom);
  lbStage?.addEventListener("click", e => { if (e.target === lbStage) closeLB(); });

  let touchX = null;
  lb?.addEventListener("touchstart", e => { touchX = e.touches[0].clientX; }, { passive: true });
  lb?.addEventListener("touchend", e => {
    if (touchX === null || lbStage.classList.contains("zoomed")) return;
    const dx = e.changedTouches[0].clientX - touchX;
    touchX = null;
    if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
  });

  const openModal = () => { gm.classList.add("open"); lock(); };
  const closeModal = () => { gm.classList.remove("open"); unlock(); };
  gm?.addEventListener("click", e => {
    if (e.target === gm || e.target.closest("[data-close]")) closeModal();
  });

  $$("[data-open]").forEach(b => b.addEventListener("click", () => openLB(Number(b.dataset.open))));

  $$("[data-all]").forEach(b => b.addEventListener("click", () => {
    if (!GAL.length) return;
    $("#gmTitle").textContent = galEl.dataset.title || "Sample screens";
    $("#gmSub").textContent = `${GAL.length} sample screens`;
    gmGrid.innerHTML = "";
    GAL.forEach((it, i) => {
      const t = document.createElement("button");
      t.type = "button";
      t.className = "thumb";
      t.setAttribute("aria-label", it.alt);
      const img = document.createElement("img");
      img.src = it.src;
      img.alt = it.alt;
      img.loading = "lazy";
      img.addEventListener("error", () => t.classList.add("missing"));
      t.append(img);
      t.addEventListener("click", () => { closeModal(); openLB(i); });
      gmGrid.append(t);
    });
    openModal();
  }));

  document.addEventListener("keydown", e => {
    if (lb?.classList.contains("open")) {
      if (e.key === "Escape") closeLB();
      else if (e.key === "ArrowRight") step(1);
      else if (e.key === "ArrowLeft") step(-1);
      else if (e.key === "z" || e.key === "Z") toggleZoom();
    } else if (gm?.classList.contains("open") && e.key === "Escape") {
      closeModal();
    }
  });

  /* ---------- FORMS -> GOOGLE SHEET (Apps Script) ---------- */
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
    const btn = $("button[type=submit]", form);
    const label = btn.textContent;

    const show = (ok, title, text, waText) => {
      notice.hidden = false;
      notice.classList.toggle("error", !ok);
      $(".ni", notice).textContent = ok ? "✓" : "!";
      $(".nt", notice).textContent = title;
      $(".np", notice).textContent = text;
      const link = $(".nl", notice);
      link.hidden = !waText;
      if (waText) link.href = waLink(waText);
      notice.scrollIntoView({ behavior: "smooth", block: "nearest" });
      clearTimeout(notice._t);
      notice._t = setTimeout(() => { notice.hidden = true; }, 10000);
    };

    form.addEventListener("submit", async e => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(form));
      if (data.website) return;              // honeypot: real users never fill this
      delete data.website;

      btn.disabled = true;
      btn.textContent = "Sending...";

      try {
        const endpoint = form.dataset.endpoint;
        if (!endpoint || endpoint.startsWith("PASTE")) {
          throw new Error("Form endpoint is not configured. Please contact the site owner.");
        }

        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "text/plain;charset=utf-8" }, // avoids CORS preflight
          body: JSON.stringify({ ...data, type: form.dataset.type, page: location.href })
        });

        const text = await res.text();
        let out = null;
        try { out = JSON.parse(text); } catch (_) { out = null; }

        if (!out) {
          throw new Error("Server did not return a valid response. Check Apps Script deployment access (Anyone) and redeploy.");
        }
        if (!out.ok) throw new Error(out.error || "Request was rejected.");

        const pdf = form.dataset.pdf;
        form.reset();
        if (pdf) {
          show(true, "Thank you!", "Your quotation is downloading. I will also contact you shortly.");
          download(pdf);
        } else {
          show(true, "Thank you!", "Your request is received. I will contact you shortly.");
        }
      } catch (err) {
        console.error("Form error:", err);
        show(false, "Could not send right now",
          err.message || "Please try again, or message us directly on WhatsApp.",
          "Hello, I need help with: " + (data.service || "automation"));
      } finally {
        btn.disabled = false;
        btn.textContent = label;
      }
    });
  });

  /* ---------- CHATBOT (rule-based, fixed answers) ---------- */
  const botBtn = $("#botBtn");
  if (botBtn) {
    const bot = $("#bot"), log = $("#botLog"), opts = $("#botOpts");
    const inService = location.pathname.includes("/services/");
    const homeUrl = inService ? "../index.html" : "index.html";
    const servicesUrl = homeUrl + "#services";
    const contactUrl = homeUrl + "#contact";
    const serviceUrl = href => (inService ? "" : "services/") + href.replace(/^services\//, "");
    const waMsg = "Hello, I have a question about an automation project.";

    const SERVICES = $$("#svcGrid .card").map(c => ({
      name: $("h3", c)?.textContent || "",
      href: c.getAttribute("href") || "",
      ico: $(".ico", c)?.textContent || ""
    }));

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
      price: "Pricing depends on your process, so every system is \"Quotation on request\".\n\nChoose the system you need and submit the quotation form. I will review your requirement and send a quotation.",
      demo: "Each system has its own page with sample screens. Open any system from the Services section to see them.",
      time: "Timeline depends on your requirement. Small systems can be ready in a few days, and larger systems are delivered in milestones. I share the exact timeline with your quotation.",
      docs: "You only need to explain your process: who does the work, which registers or files you use, and what problem you face. I handle the setup.",
      support: "Yes. I provide training, documentation and support after go-live, including fixes and upgrades.",
      about: "I am Amit, an MIS & Automation Specialist with 6 years of hands-on experience. I build systems on Google Sheets, Apps Script, WhatsApp and APIs.",
      contact: "You can reach me here:\n• Email: info@bizautosetup.com\n• WhatsApp / Mobile: +91 98557 23648\n\nOr submit the contact form and I will reply soon."
    };

    const addMsg = (text, who) => {
      const d = document.createElement("div");
      d.className = "msg " + (who === "user" ? "user-msg" : "bot-msg");
      d.textContent = text;
      log.append(d);
      log.scrollTop = log.scrollHeight;
    };
    const addLink = (text, href) => {
      const d = document.createElement("div");
      d.className = "msg bot-msg";
      const a = document.createElement("a");
      a.href = href;
      a.textContent = text;
      if (href.startsWith("http")) { a.target = "_blank"; a.rel = "noopener"; }
      d.append(a);
      log.append(d);
      log.scrollTop = log.scrollHeight;
    };
    const setOpts = list => {
      opts.innerHTML = "";
      list.forEach(o => {
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = o.label;
        b.addEventListener("click", o.run);
        opts.append(b);
      });
    };

    const mainMenu = () => setOpts(TOPICS.map(t => ({ label: t.label, run: () => answer(t.key) })));

    const serviceMenu = () => {
      setOpts([
        ...SERVICES.map(s => ({
          label: `${s.ico} ${s.name}`,
          run: () => {
            addMsg(`${s.ico} ${s.name}`, "user");
            addMsg("Details, sample screens and the quotation form are on that system's page.", "bot");
            addLink("Open details →", serviceUrl(s.href));
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
        const list = SERVICES.map(s => "• " + s.name).join("\n");
        addMsg("I build these systems:\n" + list + "\n\nWhich one would you like to know about?", "bot");
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

    const openBot = () => {
      bot.hidden = false;
      botBtn.setAttribute("aria-expanded", "true");
      if (!log.childElementCount) {
        addMsg("Hello! I am the Bizautosetup assistant. What would you like to know?", "bot");
        mainMenu();
      }
    };
    const closeBot = () => {
      bot.hidden = true;
      botBtn.setAttribute("aria-expanded", "false");
      botBtn.focus();
    };

    botBtn.addEventListener("click", () => (bot.hidden ? openBot() : closeBot()));
    $("#botClose")?.addEventListener("click", closeBot);
    document.addEventListener("keydown", e => { if (e.key === "Escape" && !bot.hidden) closeBot(); });
  }
})();