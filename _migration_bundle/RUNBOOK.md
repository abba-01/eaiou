# DO Droplet Deploy Runbook — eaiou + gitgap + scireview

**Target droplet**: 159.89.240.224 (reserved IP) — Ubuntu 24.04 x64, 2 vCPU dedicated, 8 GB RAM, 165 GB NVMe root + 500 GB volume mounted at `/mnt/volume_nyc3_1777600565990`
**Migration bundle**: `eaiou-migration-2026-04-30.tar.gz` (sha256 `36a87e17b963f5e695747cdd6d7f3a54555f274d7ad6311ded57a6d750c3f822`)
**Source**: yw.eaiou.org (34.11.195.27, GCP) — left running until cutover validated

---

## 0. Prerequisites (verify before starting)

- [ ] Droplet reachable via `ssh root@159.89.240.224`
- [ ] Volume mounted: `df -h /mnt/volume_nyc3_1777600565990` returns ~500 GB free
- [ ] Bundle uploaded: `scp eaiou-migration-2026-04-30.tar.gz root@<droplet>:/tmp/`

If volume not mounted, the 3-line mount commands you already have:

```bash
mkdir -p /mnt/volume_nyc3_1777600565990
mount -o discard,defaults,noatime /dev/disk/by-id/scsi-0DO_Volume_volume-nyc3-1777600565990 /mnt/volume_nyc3_1777600565990
echo '/dev/disk/by-id/scsi-0DO_Volume_volume-nyc3-1777600565990 /mnt/volume_nyc3_1777600565990 ext4 defaults,nofail,discard 0 0' >> /etc/fstab
```

---

## 1. System packages

```bash
apt-get update
apt-get upgrade -y
apt-get install -y \
  python3 python3-venv python3-pip python3-dev \
  mariadb-server \
  nginx \
  certbot python3-certbot-nginx \
  git curl wget unzip rsync htop tmux build-essential libssl-dev libffi-dev \
  pkg-config libmariadb-dev
```

Confirm versions:
```bash
python3 --version       # expect 3.12.x (Ubuntu 24.04 default)
mariadb --version       # expect 10.11+ or 11.x
nginx -v                # expect 1.24+
```

---

## 2. User + directory layout

```bash
# Create mae user (matches old server)
useradd -m -s /bin/bash mae
usermod -aG sudo mae

# Add SSH key for mae (the same key used to pull the bundle)
mkdir -p /home/mae/.ssh
chmod 700 /home/mae/.ssh
cat >> /home/mae/.ssh/authorized_keys <<'EOF'
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICD1gAavGaaIcMOUf5JG7so94gAqWqe7qV8Ed1dgXaeo claude-code@dev-environment
EOF
chmod 600 /home/mae/.ssh/authorized_keys
chown -R mae:mae /home/mae/.ssh
```

---

## 3. Relocate MariaDB datadir to the 500 GB volume

```bash
systemctl stop mariadb

# Move datadir
mkdir -p /mnt/volume_nyc3_1777600565990/mariadb
rsync -av /var/lib/mysql/ /mnt/volume_nyc3_1777600565990/mariadb/
mv /var/lib/mysql /var/lib/mysql.original
ln -s /mnt/volume_nyc3_1777600565990/mariadb /var/lib/mysql
chown -R mysql:mysql /mnt/volume_nyc3_1777600565990/mariadb

# AppArmor (Ubuntu) — allow mysqld to access the new path
cat >> /etc/apparmor.d/local/usr.sbin.mysqld <<'EOF'
/mnt/volume_nyc3_1777600565990/mariadb/ r,
/mnt/volume_nyc3_1777600565990/mariadb/** rwk,
EOF
systemctl reload apparmor

systemctl start mariadb
mariadb -e "SHOW DATABASES;"  # verify
```

---

## 4. Extract migration bundle

```bash
cd /tmp
tar xzf eaiou-migration-2026-04-30.tar.gz
ls eaiou-migration-2026-04-30/
```

---

## 5. Restore eaiou database

```bash
# Create DB + user (cred values: pull from migration bundle's app .env)
EAIOU_DB_PASS=$(grep -E '^DB_PASS' /tmp/eaiou-migration-2026-04-30/apps/eaiou/.env | cut -d= -f2- | tr -d '"' | tr -d "'")
mariadb <<SQL
CREATE DATABASE eaiou CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'eaiou'@'localhost' IDENTIFIED BY '$EAIOU_DB_PASS';
GRANT ALL PRIVILEGES ON eaiou.* TO 'eaiou'@'localhost';
FLUSH PRIVILEGES;
SQL

# Restore schema + data
mariadb eaiou < /tmp/eaiou-migration-2026-04-30/databases/eaiou.sql
mariadb eaiou -e "SHOW TABLES;" | head
```

---

## 6. Restore gitgap database (schema only — data regens from external APIs)

```bash
mariadb <<SQL
CREATE DATABASE gitgap CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'gitgap'@'localhost' IDENTIFIED BY '$(openssl rand -base64 24)';
GRANT ALL PRIVILEGES ON gitgap.* TO 'gitgap'@'localhost';
FLUSH PRIVILEGES;
SQL

mariadb gitgap < /tmp/eaiou-migration-2026-04-30/apps/gitgap/schema/gitgap_install.sql
mariadb gitgap < /tmp/eaiou-migration-2026-04-30/apps/gitgap/schema/migration_001_gap_classification.sql
```

---

## 7. Place applications on the volume

Apps live on the 500 GB volume so they're sized for growth + decoupled from the OS disk.

```bash
mkdir -p /mnt/volume_nyc3_1777600565990/apps
rsync -a /tmp/eaiou-migration-2026-04-30/apps/ /mnt/volume_nyc3_1777600565990/apps/

# Symlink into /home/mae for path compatibility with systemd units
ln -s /mnt/volume_nyc3_1777600565990/apps/eaiou     /home/mae/eaiou
ln -s /mnt/volume_nyc3_1777600565990/apps/gitgap    /home/mae/gitgap
ln -s /mnt/volume_nyc3_1777600565990/apps/scireview /home/mae/scireview
ln -s /mnt/volume_nyc3_1777600565990/apps/cmslite   /home/mae/cmslite
chown -R mae:mae /mnt/volume_nyc3_1777600565990/apps
```

---

## 8. Recreate Python venvs

```bash
for app in eaiou gitgap scireview; do
  if [ -d /home/mae/$app ]; then
    sudo -u mae python3 -m venv /home/mae/$app/venv
    sudo -u mae /home/mae/$app/venv/bin/pip install --upgrade pip wheel
    if [ -f /home/mae/$app/requirements.txt ]; then
      sudo -u mae /home/mae/$app/venv/bin/pip install -r /home/mae/$app/requirements.txt
    fi
  fi
done
```

---

## 9. nginx vhosts

```bash
cp /tmp/eaiou-migration-2026-04-30/nginx/eaiou     /etc/nginx/sites-available/eaiou
cp /tmp/eaiou-migration-2026-04-30/nginx/gitgap    /etc/nginx/sites-available/gitgap
cp /tmp/eaiou-migration-2026-04-30/nginx/scireview /etc/nginx/sites-available/scireview

ln -s /etc/nginx/sites-available/eaiou     /etc/nginx/sites-enabled/
ln -s /etc/nginx/sites-available/gitgap    /etc/nginx/sites-enabled/
ln -s /etc/nginx/sites-available/scireview /etc/nginx/sites-enabled/

# Remove default
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx
```

---

## 10. systemd units

```bash
cp /tmp/eaiou-migration-2026-04-30/systemd/eaiou.service     /etc/systemd/system/
cp /tmp/eaiou-migration-2026-04-30/systemd/gitgap.service    /etc/systemd/system/
cp /tmp/eaiou-migration-2026-04-30/systemd/scireview.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable --now eaiou gitgap scireview

# Verify
systemctl status eaiou gitgap scireview --no-pager | head -30
```

---

## 11. Pre-DNS validation (test by Host header)

```bash
curl -I -H "Host: eaiou.org" http://localhost/
curl -I -H "Host: gitgap.org" http://localhost/
curl -I -H "Host: yw.eaiou.org" http://localhost/
```

All three should return non-error responses (302, 200, etc.). If any returns 5xx, debug before DNS cutover.

---

## 12. DNS cutover

At your registrar (or DigitalOcean DNS if delegated):

| Record | Type | Target |
|---|---|---|
| `eaiou.org` | A | 159.89.240.224 |
| `www.eaiou.org` | A | 159.89.240.224 |
| `gitgap.org` | A | 159.89.240.224 |
| `www.gitgap.org` | A | 159.89.240.224 |
| `edm.aybllc.org` | A | 159.89.240.224 (already if scireview lives there) |

**Lower TTL to 300 seconds before cutover** so propagation is fast. Verify post-cutover:

```bash
dig @1.1.1.1 eaiou.org +short  # expect 159.89.240.224
dig @8.8.8.8 eaiou.org +short
```

---

## 13. Let's Encrypt certificates (after DNS lands)

```bash
certbot --nginx \
  -d eaiou.org -d www.eaiou.org \
  -d gitgap.org -d www.gitgap.org \
  -d edm.aybllc.org \
  --non-interactive --agree-tos -m doctor.eric.martin@gmail.com
```

certbot rewrites the nginx vhosts to add the SSL block + sets up auto-renewal.

---

## 14. Validation

```bash
# HTTPS reachability
curl -I https://eaiou.org/
curl -I https://gitgap.org/

# eaiou DB
mariadb eaiou -e "SELECT COUNT(*) FROM tblstaff;"  # or whichever table is live

# Service log tails (should be quiet)
journalctl -u eaiou -n 20
journalctl -u gitgap -n 20

# Confirm volume usage
df -h /mnt/volume_nyc3_1777600565990
```

---

## 15. 48-hour soak before decommissioning old GCP server

Leave `34.11.195.27` running for 48 hours after DNS cutover. If anything misbehaves on DO, revert DNS in 5 minutes.

After 48 hours of clean operation:
- Power down the GCP instance (do NOT delete yet)
- Wait another 7 days for any "I should have backed that up" realization
- Then delete the GCP instance + release IPs

---

## Rollback (if needed before 48h is up)

```bash
# At DNS registrar — point records back to old IP
eaiou.org → 34.11.195.27
gitgap.org → 34.11.195.27
```

That's it. The old server is still running the old code; reverting DNS reverts the cutover.

---

## Provenance

- Bundle source: yw.eaiou.org (34.11.195.27 / GCP)
- Bundle date: 2026-04-30 03:36 UTC (server time)
- Bundle sha256: `36a87e17b963f5e695747cdd6d7f3a54555f274d7ad6311ded57a6d750c3f822`
- Local mirror: `/scratch/repos/eaiou/_migration_bundle/eaiou-migration-2026-04-30.tar.gz`
- Excluded (regenerate on droplet): `.venv/`, `__pycache__/`, `.git/`, `node_modules/`, `/etc/letsencrypt/`, `/var/lib/mysql/` raw datadir
- Apps captured: eaiou (59M), gitgap (21M), scireview (712K), cmslite (648K)
- DBs captured: eaiou.sql (288K dump) + eaiou_backup_pre_existing.sql (172K) + 11 schema migration SQLs in app trees

Per `feedback_artifact_hash_naming.md`: bundle filename + checksum recorded above. After git commit on droplet, re-anchor with commit hash.
