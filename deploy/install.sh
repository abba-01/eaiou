#!/bin/bash
# eaiou CMS — VM Bootstrap Install Script
# Run as root on fresh Debian 12 (Bookworm)
# Author: Eric D. Martin | ORCID 0009-0006-5944-1742
# Usage: bash install.sh

set -e

EAIOU_DIR="/opt/eaiou"
EAIOU_USER="eaiou"
DB_NAME="eaiou"
DB_USER="eaiou_db"
DB_PASS=""  # Set before running — or script will prompt

echo "=== eaiou CMS Install ==="

# ── 1. System update ──────────────────────────────────────────────────────────
apt-get update && apt-get upgrade -y
apt-get install -y \
    nginx \
    python3.12 python3.12-venv python3-pip \
    mariadb-server \
    certbot python3-certbot-nginx \
    apache2-utils \
    git curl ufw

# ── 2. Firewall ───────────────────────────────────────────────────────────────
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# ── 3. MariaDB setup ──────────────────────────────────────────────────────────
systemctl enable --now mariadb

if [ -z "$DB_PASS" ]; then
    read -s -p "Set eaiou database password: " DB_PASS
    echo
fi

mysql -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';"
mysql -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

echo "Database created: ${DB_NAME}"

# ── 4. App user and directory ─────────────────────────────────────────────────
useradd --system --home ${EAIOU_DIR} --shell /bin/bash ${EAIOU_USER} 2>/dev/null || true
mkdir -p ${EAIOU_DIR}
chown ${EAIOU_USER}:${EAIOU_USER} ${EAIOU_DIR}

# ── 5. Python venv ────────────────────────────────────────────────────────────
python3.12 -m venv ${EAIOU_DIR}/venv
${EAIOU_DIR}/venv/bin/pip install --upgrade pip
${EAIOU_DIR}/venv/bin/pip install \
    fastapi \
    "uvicorn[standard]" \
    gunicorn \
    sqlalchemy \
    pymysql \
    cryptography \
    jinja2 \
    python-multipart \
    python-dotenv \
    passlib[bcrypt] \
    httpx

chown -R ${EAIOU_USER}:${EAIOU_USER} ${EAIOU_DIR}/venv

# ── 6. Schema install ─────────────────────────────────────────────────────────
if [ -f "${EAIOU_DIR}/schema/eaiou_install_canonical.sql" ]; then
    mysql ${DB_NAME} < ${EAIOU_DIR}/schema/eaiou_install_canonical.sql
    echo "Schema installed."
else
    echo "WARN: Schema file not found at ${EAIOU_DIR}/schema/eaiou_install_canonical.sql — install manually."
fi

# ── 7. .env file ──────────────────────────────────────────────────────────────
cat > ${EAIOU_DIR}/.env << EOF
DB_HOST=localhost
DB_PORT=3306
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASS=${DB_PASS}
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ENVIRONMENT=development
SITE_OFFLINE=true
EOF
chmod 600 ${EAIOU_DIR}/.env
chown ${EAIOU_USER}:${EAIOU_USER} ${EAIOU_DIR}/.env

# ── 8. nginx basic_auth credentials ──────────────────────────────────────────
read -p "Invite-only username: " AUTH_USER
htpasswd -c /etc/nginx/.eaiou_htpasswd ${AUTH_USER}

# ── 9. nginx config ───────────────────────────────────────────────────────────
cat > /etc/nginx/sites-available/eaiou << 'NGINX'
server {
    listen 80;
    server_name eaiou.org www.eaiou.org;

    # Invite-only gate
    auth_basic "eaiou — restricted";
    auth_basic_user_file /etc/nginx/.eaiou_htpasswd;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/eaiou/app/static;
        expires 1d;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/eaiou /etc/nginx/sites-enabled/eaiou
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# ── 10. systemd service ───────────────────────────────────────────────────────
cat > /etc/systemd/system/eaiou.service << EOF
[Unit]
Description=eaiou CMS
After=network.target mariadb.service

[Service]
User=${EAIOU_USER}
Group=${EAIOU_USER}
WorkingDirectory=${EAIOU_DIR}
EnvironmentFile=${EAIOU_DIR}/.env
ExecStart=${EAIOU_DIR}/venv/bin/gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile ${EAIOU_DIR}/logs/access.log \
    --error-logfile ${EAIOU_DIR}/logs/error.log
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

mkdir -p ${EAIOU_DIR}/logs
chown ${EAIOU_USER}:${EAIOU_USER} ${EAIOU_DIR}/logs

systemctl daemon-reload
systemctl enable eaiou

echo ""
echo "=== Install complete ==="
echo "Next steps:"
echo "  1. Copy app/ directory to ${EAIOU_DIR}/app/"
echo "  2. Run: systemctl start eaiou"
echo "  3. Run: certbot --nginx -d eaiou.org -d www.eaiou.org"
echo "  4. Point eaiou.org DNS A record to this VM's external IP"
