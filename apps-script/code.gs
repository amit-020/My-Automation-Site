/**
 * Bizautosetup lead backend (Google Apps Script Web App)
 *
 * SETUP
 * 1. Google Sheet mein tab "Leads" banayein. First row mein ye headers:
 *    Timestamp | Type | Name | Company | Phone | Email | Service | Message | Page | Status
 * 2. Extensions > Apps Script kholkar ye code paste karein, save karein.
 * 3. Deploy > New deployment > Type: Web app
 *    Execute as: Me  |  Who has access: Anyone  →  Deploy
 * 4. Web app URL copy karke build.py ki CFG["sheet_url"] mein paste karein, phir build.py chalayein.
 *
 * Code badalne par: Deploy > Manage deployments > Edit > Version: New version > Deploy
 * (URL same rehta hai.)
 */

const SHEET_NAME = "Leads";
const NOTIFY_EMAIL = "info@bizautosetup.com";
const MAX_LEN = 2000;

function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    const d = JSON.parse((e && e.postData && e.postData.contents) || "{}");

    // Honeypot: bots hidden "website" field bharte hain. Success dikhao, kuch save mat karo.
    if (d.website) return json({ ok: true });

    clean(d);
    validate(d);

    lock.waitLock(10000);
    const sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
    if (!sh) throw new Error("Sheet '" + SHEET_NAME + "' not found");

    sh.appendRow([
      new Date(), d.type, d.name, d.company || "", d.phone,
      d.email || "", d.service || "", d.message || "", d.page || "", "New"
    ]);

    notify(d);
    return json({ ok: true });
  } catch (err) {
    return json({ ok: false, error: String(err.message || err) });
  } finally {
    if (lock.hasLock()) lock.releaseLock();
  }
}

// Browser mein Web App URL kholne par health check
function doGet() {
  return json({ ok: true, status: "Bizautosetup lead endpoint is live" });
}

function clean(d) {
  Object.keys(d).forEach(k => {
    if (typeof d[k] === "string") d[k] = d[k].trim().slice(0, MAX_LEN);
  });
  d.type = d.type === "Quotation" ? "Quotation" : "Contact";
}

function validate(d) {
  if (!d.name) throw new Error("Name is required");
  if (!/^\+?[0-9 ]{10,15}$/.test(d.phone || "")) throw new Error("Valid phone number is required");
  if (d.email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(d.email)) throw new Error("Invalid email");
}

// Email alert. Mail fail hone par bhi lead Sheet mein already save ho chuki hai.
function notify(d) {
  try {
    const body = Object.keys(d)
      .filter(k => k !== "website")
      .map(k => k + ": " + d[k])
      .join("\n");
    MailApp.sendEmail(NOTIFY_EMAIL, "New " + d.type + " lead: " + (d.service || d.name), body);
  } catch (err) {
    console.error("Notify failed: " + err);
  }
}

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}