/**
 * EAIOU Theme Switcher
 * Injects a toggle bar + loads theme CSS overrides for folder 2 screens.
 * Themes: Original (neutral), Sky (folder-3 style), PeerTrail (multi-bright)
 */
(function() {
    const THEMES = {
        original: { label: 'Original', css: null, color: '#a3a3a3' },
        sky:      { label: 'Sky',      css: 'theme-sky.css', color: '#0ea5e9' },
        peertrail:{ label: 'PeerTrail',css: 'theme-peertrail.css', color: '#6c5ce7' },
    };

    let activeTheme = localStorage.getItem('eaiou-theme') || 'original';
    let linkEl = null;

    function applyTheme(name) {
        activeTheme = name;
        localStorage.setItem('eaiou-theme', name);

        if (linkEl) linkEl.remove();

        const theme = THEMES[name];
        if (theme.css) {
            linkEl = document.createElement('link');
            linkEl.rel = 'stylesheet';
            linkEl.href = theme.css;
            linkEl.id = 'eaiou-theme-css';
            document.head.appendChild(linkEl);
        } else {
            linkEl = null;
        }

        // Update button states
        document.querySelectorAll('.eaiou-theme-btn').forEach(btn => {
            const isActive = btn.dataset.theme === name;
            btn.style.background = isActive ? THEMES[btn.dataset.theme].color : 'transparent';
            btn.style.color = isActive ? '#fff' : '#94a3b8';
            btn.style.borderColor = THEMES[btn.dataset.theme].color;
        });
    }

    function createSwitcher() {
        const bar = document.createElement('div');
        bar.id = 'eaiou-switcher';
        bar.style.cssText = 'position:fixed;top:12px;right:12px;z-index:99999;' +
            'background:rgba(15,23,42,0.92);backdrop-filter:blur(12px);' +
            'padding:6px 10px;border-radius:10px;display:flex;gap:6px;' +
            'align-items:center;border:1px solid rgba(255,255,255,0.1);' +
            'box-shadow:0 4px 20px rgba(0,0,0,0.3);';

        const label = document.createElement('span');
        label.textContent = 'Theme';
        label.style.cssText = 'color:#64748b;font-size:11px;font-family:Inter,sans-serif;' +
            'font-weight:600;margin-right:4px;letter-spacing:0.5px;text-transform:uppercase;';
        bar.appendChild(label);

        for (const [key, theme] of Object.entries(THEMES)) {
            const btn = document.createElement('button');
            btn.className = 'eaiou-theme-btn';
            btn.dataset.theme = key;
            btn.textContent = theme.label;
            btn.style.cssText = 'padding:4px 12px;border-radius:6px;font-size:11px;' +
                'font-family:Inter,sans-serif;font-weight:500;cursor:pointer;' +
                'border:1.5px solid ' + theme.color + ';transition:all 0.15s;' +
                'background:transparent;color:#94a3b8;';
            btn.addEventListener('click', () => applyTheme(key));
            bar.appendChild(btn);
        }

        document.body.appendChild(bar);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => { createSwitcher(); applyTheme(activeTheme); });
    } else {
        createSwitcher(); applyTheme(activeTheme);
    }
})();
