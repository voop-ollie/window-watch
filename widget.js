// Window Watch — Scriptable widget (medium / full-width)
// Install: paste into a new Scriptable script, add to home screen as a Medium widget

const GIST_URL = "https://gist.githubusercontent.com/voop-ollie/bd24c63bd7e129c86942db6ed67f9008/raw/window-watch-status.json"
const DASHBOARD_URL = "https://voop-ollie.github.io/window-watch/"

const THEME = {
  open: {
    bg:     new Color("#0f3460"),
    accent: new Color("#4db6ff"),
    label:  "OPEN",
    hint:   "let the air through",
  },
  close: {
    bg:     new Color("#7b1e1e"),
    accent: new Color("#ff8c8c"),
    label:  "CLOSE",
    hint:   "hold the cool in",
  },
  unknown: {
    bg:     new Color("#1a1a2e"),
    accent: new Color("#888888"),
    label:  "—",
    hint:   "waiting for data",
  },
}

function timeAgo(utcString) {
  if (!utcString) return "never"
  const diff = Math.floor((Date.now() - new Date(utcString).getTime()) / 60000)
  if (diff < 1) return "just now"
  if (diff < 60) return `${diff}m ago`
  return `${Math.floor(diff / 60)}h ago`
}

async function fetchStatus() {
  try {
    const req = new Request(GIST_URL + "?t=" + Date.now())
    return await req.loadJSON()
  } catch (e) {
    return null
  }
}

const data = await fetchStatus()
const status = data?.status ?? "unknown"
const theme = THEME[status] ?? THEME.unknown

const widget = new ListWidget()
widget.backgroundColor = theme.bg
widget.setPadding(16, 20, 16, 20)
widget.url = DASHBOARD_URL

// Layout: two columns
const row = widget.addStack()
row.layoutHorizontally()
row.centerAlignContent()

// ── Left column: status ──────────────────────
const left = row.addStack()
left.layoutVertically()
left.size = new Size(160, 0)

const labelText = left.addText(theme.label)
labelText.font = Font.boldSystemFont(40)
labelText.textColor = theme.accent
labelText.minimumScaleFactor = 0.7

left.addSpacer(4)

const hintText = left.addText(theme.hint)
hintText.font = Font.systemFont(13)
hintText.textColor = new Color(theme.accent.hex, 0.6)

row.addSpacer()

// ── Right column: details ────────────────────
const right = row.addStack()
right.layoutVertically()

if (data?.outdoor_c != null) {
  const tempText = right.addText(`${data.outdoor_c.toFixed(1)}°C outside`)
  tempText.font = Font.systemFont(15)
  tempText.textColor = new Color("#ffffff", 0.85)
  tempText.rightAlignText()
  right.addSpacer(4)
}

if (data?.close_above_c != null) {
  const threshText = right.addText(`Close >${data.close_above_c}°  Open <${data.open_below_c}°`)
  threshText.font = Font.systemFont(11)
  threshText.textColor = new Color("#ffffff", 0.35)
  threshText.rightAlignText()
  right.addSpacer(8)
}

const updatedText = right.addText(`Updated ${timeAgo(data?.updated_utc)}`)
updatedText.font = Font.systemFont(11)
updatedText.textColor = new Color("#ffffff", 0.3)
updatedText.rightAlignText()

Script.setWidget(widget)
widget.presentMedium()
Script.complete()
