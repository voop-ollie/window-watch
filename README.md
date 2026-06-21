# Window Watch

Buzzes your phone when outside air gets warm enough that you should close the
windows, and again in the evening when it's cool enough to reopen. Reads outdoor
temperature from Open-Meteo and your indoor temperature from myVAILLANT.

You get **one** notification per change of state, not one every 30 minutes.

---

## 1. Get the phone app (ntfy)

1. Install **ntfy** (App Store / Play Store / F-Droid). It's free.
2. Pick a **private topic name** — treat it like a password, because anyone who
   knows it can read your alerts. Use something unguessable, e.g.
   `window-watch-ollie-7fj29x`.
3. In the app, tap **+** and subscribe to that topic.

That's all the phone needs.

## 2. Put this folder in a **private** GitHub repo

Your Vaillant login is stored as a repo secret. Keep the repo **private** so the
credentials and your ntfy topic stay yours.

```
git init && git add . && git commit -m "window watch"
# create a PRIVATE repo on github.com, then:
git remote add origin git@github.com:<you>/window-watch.git
git push -u origin main
```

## 3. Add your secrets and variables

In the repo: **Settings → Secrets and variables → Actions**.

Under **Secrets** (encrypted):
- `NTFY_TOPIC` — your topic from step 1
- `VAILLANT_USER` — your myVAILLANT email
- `VAILLANT_PASS` — your myVAILLANT password

Under **Variables** (optional — defaults are Tower Hamlets):
- `LAT` = `51.5128`
- `LON` = `-0.0566`

## 4. Confirm your country key (one-time)

The library needs the right country string. Locally:

```
pip install myPyllant
python -m myPyllant.export -h          # lists valid --country values
```

`unitedkingdom` is set as the default in the workflow; change it there if the
list shows something different for you.

## 5. Test it

Repo → **Actions → window-watch → Run workflow**. Within a few seconds either
your phone buzzes (if it's a close/open moment) or the run log shows the current
reading, e.g. `outdoor=24.1 indoor=22.0 last=open -> close`.

After that it runs itself every 30 minutes.

---

## Tuning

All optional, set as repo Variables (or env vars if running locally):

- `HYSTERESIS` (default `1.5`) — how far outside must drop *below* inside before
  the "reopen" alert fires. Bigger = fewer borderline pings.
- `INDOOR_FALLBACK` (default `22`) — indoor °C used if Vaillant is briefly
  unreachable (their API has occasional outages).

## Running on a Raspberry Pi / Home Assistant box instead

More reliable than GitHub's scheduler if you have an always-on machine. Same
script:

```
pip install -r requirements.txt
# add a cron line (every 30 min):
*/30 * * * * cd /home/pi/window-watch && \
  NTFY_TOPIC=... VAILLANT_USER=... VAILLANT_PASS=... \
  VAILLANT_COUNTRY=unitedkingdom INDOOR_FALLBACK=22 \
  /usr/bin/python3 window_watch.py >> watch.log 2>&1
```

The local `state.json` handles change-detection automatically — no caching
needed.

## Notes

- This uses an **unofficial** Vaillant API library. It works well but Vaillant
  can change or rate-limit the API; if indoor reads fail, the script falls back
  to `INDOOR_FALLBACK` so you still get outdoor-based alerts.
- The decision is air-temperature only. On a sunny day, closing sun-side blinds
  *before* the crossover still helps against radiant gain.
