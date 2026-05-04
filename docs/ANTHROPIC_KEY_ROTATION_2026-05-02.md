# Anthropic API Key Rotation Procedure

**Trigger:** CWO audit finding C-2 (2026-05-02) — `ANTHROPIC_API_KEY` is in
`/home/mae/eaiou/.env` on the production droplet. Until rotated, treat as
compromised: any path-traversal flaw, accidental `.env` exposure, or droplet
compromise leaks the key.

**Owner:** Eric. Mae cannot rotate (Anthropic console access is biometric).

**Estimated time:** 10 minutes if you have console access ready; 25 minutes
if you need to verify the new key works against the live eaiou agents and
checksubmit handlers before retiring the old one.

---

## Pre-flight checks (1 minute)

```bash
# 1. Confirm old key is still in droplet .env (you'll need to know which line to replace)
ssh -p 63043 mae@edm.aybllc.org "grep ANTHROPIC_API_KEY /home/mae/eaiou/.env | head -1"

# 2. Confirm Mae's local /root/.env doesn't have a stale copy
grep ANTHROPIC_API_KEY /root/.env
# Expected: empty or stale; we never run agents from local box, so a stale
# copy here is low-risk but should still be cleared.

# 3. Confirm the eaiou service uses .env (no other ENV-injection path)
ssh -p 63043 mae@edm.aybllc.org "systemctl cat eaiou | grep -i environment"
# Expected: shows EnvironmentFile=/home/mae/eaiou/.env or similar
```

## Step 1 — Issue the new key (5 minutes)

1. Go to https://console.anthropic.com/settings/keys
2. Click **Create Key**
3. Name it: `eaiou-prod-2026-05-02` (date-suffix so future audits can correlate
   key→creation-event)
4. Set the workspace + permissions same as the old key
5. Copy the new key — you have ONE chance; the console doesn't show it again
6. Paste it into a temporary local file `~/anthropic_new_key.txt` (delete after
   step 4 below)

## Step 2 — Hot-swap on droplet (3 minutes)

```bash
# 1. SCP the new key file up
scp -P 63043 ~/anthropic_new_key.txt mae@edm.aybllc.org:~/

# 2. SSH in and replace the line in .env
ssh -p 63043 mae@edm.aybllc.org

# On droplet:
NEW_KEY=$(cat ~/anthropic_new_key.txt | tr -d '[:space:]')
# Snapshot the .env first
cp /home/mae/eaiou/.env /home/mae/backups/db/eaiou_env_$(date +%Y%m%d_%H%M%S)_pre_rotate.bak
# Replace the line — keep the variable name + the rest of the file intact
sed -i.bak "s|^ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=${NEW_KEY}|" /home/mae/eaiou/.env

# 3. Confirm the change took
grep "^ANTHROPIC_API_KEY=" /home/mae/eaiou/.env | head -1

# 4. Wipe the temp file
shred -u ~/anthropic_new_key.txt
```

## Step 3 — Restart eaiou service (1 minute)

```bash
# Still on droplet:
sudo systemctl restart eaiou
sudo systemctl status eaiou --no-pager | head -10
# Expected: active (running)

# Verify the service is reading the new key (don't print the key itself):
journalctl -u eaiou --since "1 min ago" | head -20
# Look for: no "credit balance too low" / "invalid api key" errors
```

## Step 4 — Smoke-test the new key (5 minutes)

```bash
# On droplet:
cd /home/mae/eaiou && source venv/bin/activate

# 1. Verify the agent orchestrator can start (does a preflight ping)
python3 -c "
import os, anthropic
os.environ['ANTHROPIC_API_KEY']  # raise KeyError if missing
client = anthropic.Anthropic()
resp = client.messages.create(
    model='claude-haiku-4-5-20251001',
    max_tokens=10,
    messages=[{'role': 'user', 'content': 'ping'}]
)
print('OK — model:', resp.model, 'usage:', resp.usage.output_tokens, 'output tokens')
"
# Expected: 'OK — model: claude-haiku-4-5-...' line. Any error means the new
# key isn't authenticating; back to step 1 with a fresh key.

# 2. Smoke-test a checksubmit handler (real call, ~$0.01)
CHECKSUBMIT_DRY_RUN= python3 -c "
import sys; sys.path.insert(0, '.')
from app.services.review_handlers import dispatch
result = dispatch('scope_check', {'manuscript_text': 'A short test manuscript about cell biology.', 'target_venue': 'Cell'}, {})
print('reasoning:', result.get('reasoning', '')[:200])
print('iid:', result.get('iid'))
"
# Expected: real reasoning text + IID disclosure with a real instance_hash
# (NOT the dry-run hash 5533163768d2eac1).
```

## Step 5 — Retire the old key (1 minute)

ONLY after step 4 passes:

1. Go back to https://console.anthropic.com/settings/keys
2. Find the old key (named with the previous date or `eaiou-prod` etc)
3. Click **Disable** (don't delete — disabling preserves the key id in your
   audit log)
4. Confirm disabled.

**Do NOT skip this step.** Until the old key is disabled, both keys work and
the leaked key is still live.

---

## Post-rotation verification

```bash
# On droplet, watch the log for ~5 minutes for any auth failures:
journalctl -u eaiou -f
# Cmd+C when satisfied no auth errors are firing
```

Update `project_current_state.md` with:
- Rotation timestamp
- New key name (eaiou-prod-2026-05-02)
- Old key disabled timestamp
- Smoke-test scope_check result hash (proves the new key actually invokes Anthropic)

Update Perfex audit ledger (Project 17 task 63 sub-item or equivalent):
- Mark C-2 as resolved with rotation timestamp.

---

## Rollback (if step 4 fails)

If the new key fails smoke-test:

```bash
ssh -p 63043 mae@edm.aybllc.org
# Restore the .env backup
cp /home/mae/eaiou/.env.bak /home/mae/eaiou/.env
sudo systemctl restart eaiou
# Verify old key is back
grep "^ANTHROPIC_API_KEY=" /home/mae/eaiou/.env | head -1
sudo systemctl status eaiou --no-pager | head -5
```

Then go back to console, re-issue a new key, repeat from step 1. Do NOT leave
the old key disabled if rollback was needed — re-enable it on the console.

---

## Why we rotate (not just delete + re-issue once)

* Anthropic doesn't support key versioning; rotation IS delete-and-replace.
* Keeping the old key alive during step 4 means a 1-2 minute window where
  both keys work — that's the safe handover. Disabling the old key BEFORE
  the new one's verified means downtime.
* Disabling (not deleting) the old key preserves the audit trail. If you
  ever need to forensically verify whether usage at time T was the old or
  new key, the disabled state on the console is the witness.

## What this rotation does NOT do

* Does NOT update any client-side keys (we don't have any — the key is
  server-only).
* Does NOT change the eaiou_iid_providers.api_key_encrypted entries
  (those are author-supplied keys, not the platform key; they're a
  different rotation cycle).
* Does NOT clear the leaked key from past audit logs / log archives —
  if log archives might contain the leaked key, those need separate
  scrubbing.
