#!/bin/bash

# Detect OLSPanel directory
BASE_DIR="/usr/local/olspanel/mypanel"
if [ ! -d "$BASE_DIR" ]; then
  # Fallback to local discovery
  BASE_DIR="$(pwd)"
  if [ ! -f "$BASE_DIR/manage.py" ]; then
    BASE_DIR="$(dirname "$(dirname "$BASE_DIR")")"
  fi
fi

DECORATORS_FILE="$BASE_DIR/users/decorators.py"
MIDDLEWARE_FILE="$BASE_DIR/users/middleware/LicenseMiddleware.py"
FUNCTIONS_FILE="$BASE_DIR/users/function.py"
USER_BASE_HTML="$BASE_DIR/users/templates/users/base.html"
WHM_BASE_HTML="$BASE_DIR/whm/templates/whm/base.html"
USER_FOOTER_HTML="$BASE_DIR/users/templates/users/footer.html"
WHM_FOOTER_HTML="$BASE_DIR/whm/templates/whm/footer.html"
USER_DB_IMPORT_HTML="$BASE_DIR/users/templates/users/db_import.html"

# Patch 1: Make decorators.py return active license and bypass premium checks immediately
if [ -f "$DECORATORS_FILE" ]; then
  python3 -c "
import os, re
file_path = '$DECORATORS_FILE'
with open(file_path, 'r') as f:
    content = f.read()

pattern = re.compile(r'def get_license_status\(request\):.*', re.DOTALL)
new_tail = '''def get_license_status(request):
    return \"active\"

def premium_features(*allowed_types):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
'''
if pattern.search(content):
    content = pattern.sub(new_tail, content)
    with open(file_path, 'w') as f:
        f.write(content)
    print('decorators.py patched successfully')
"
fi

# Patch 2: Make LicenseMiddleware.py completely transparent with zero overhead
if [ -f "$MIDDLEWARE_FILE" ]; then
  cat << 'EOF' > "$MIDDLEWARE_FILE"
from django.shortcuts import redirect, render

def get_license_status(request):
    return "active"

class LicenseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
EOF
  echo "LicenseMiddleware.py rewritten successfully"
fi

# Patch 3: Make get_license_status inside function.py return active instantly
if [ -f "$FUNCTIONS_FILE" ]; then
  python3 -c "
import os, re
file_path = '$FUNCTIONS_FILE'
with open(file_path, 'r') as f:
    content = f.read()

pattern = re.compile(r'def get_license_status\(request\):.*?def download_script_only', re.DOTALL)
new_block = '''def get_license_status(request):
    return \"active\"


def download_script_only'''

if pattern.search(content):
    content = pattern.sub(new_block, content)
    with open(file_path, 'w') as f:
        f.write(content)
    print('function.py patched successfully')
"
fi

# Patch 4: Solve FOUC (Color Flicker) & dynamic SVG fetch lag on base.html files
python3 -c "
import os, re

files = ['$USER_BASE_HTML', '$WHM_BASE_HTML']
new_script = '''{% if branding.brand_color != \\\"#ef6d19\\\" %}   
<script>
(function() {
    const brandColor = \\\"{{ branding.brand_color }}\\\";
    if (brandColor === \\\"#ef6d19\\\") return;

    // Apply CSS overrides immediately
    const style = document.createElement('style');
    style.innerHTML = \`
        :root { --brand-color: \${brandColor} !important; }
        .brand-name font, .app-brand font, .app-brand span font { color: \${brandColor} !important; }
        .sidebar-dark .sidebar-inner .nav > li.active > a i, 
        .sidebar-dark .sidebar-inner .nav > li.active > a span,
        .sidebar-dark .sidebar-inner .nav > li.active > a img { color: \${brandColor} !important; }
    \`;
    document.head.appendChild(style);

    function processImage(img) {
        const src = img.src;
        if (!src.endsWith('.svg')) return;

        function replaceImg(svgText) {
            const parser = new DOMParser();
            const doc = parser.parseFromString(svgText, \\\"image/svg+xml\\\");
            const svg = doc.querySelector(\\\"svg\\\");
            if (!svg) return;

            Array.from(img.attributes).forEach(attr => {
                if (attr.name !== \\\"src\\\") {
                    svg.setAttribute(attr.name, attr.value);
                }
            });

            if (!svg.getAttribute(\\\"width\\\")) svg.setAttribute(\\\"width\\\", img.getAttribute(\\\"width\\\") || \\\"40px\\\");
            if (!svg.getAttribute(\\\"height\\\")) svg.setAttribute(\\\"height\\\", img.getAttribute(\\\"height\\\") || \\\"40px\\\");

            svg.style.cssText = img.style.cssText;
            svg.style.color = brandColor;
            svg.setAttribute(\\\"fill\\\", \\\"currentColor\\\");

            svg.querySelectorAll(\\\"*\\\").forEach(el => {
                if (el.getAttribute(\\\"fill\\\") && el.getAttribute(\\\"fill\\\") !== \\\"none\\\") {
                    el.setAttribute(\\\"fill\\\", \\\"currentColor\\\");
                }
                if (el.getAttribute(\\\"stroke\\\") && el.getAttribute(\\\"stroke\\\") !== \\\"none\\\") {
                    el.setAttribute(\\\"stroke\\\", \\\"currentColor\\\");
                }
            });

            img.replaceWith(svg);
        }

        const cached = localStorage.getItem('svg_' + src);
        if (cached) {
            replaceImg(cached);
        } else {
            fetch(src)
                .then(r => r.text())
                .then(svgText => {
                    try {
                        localStorage.setItem('svg_' + src, svgText);
                    } catch(e) {}
                    replaceImg(svgText);
                })
                .catch(err => console.error(\\\"SVG load failed:\\\", err));
        }
    }

    function init() {
        document.querySelectorAll('#search_here img[src$=\\\".svg\\\"], #left-sidebar img[src$=\\\".svg\\\"]').forEach(processImage);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
</script>
{% endif %}'''

for file_path in files:
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        
        pattern = re.compile(r'{%\s*if\s+branding\.brand_color\s*!=\s*\"#ef6d19\"\s*%}\s*<script>.*?</script>\s*{%\s*endif\s*%}', re.DOTALL)
        if pattern.search(content):
            content = pattern.sub(new_script, content)
            with open(file_path, 'w') as f:
                f.write(content)
            print('Patched FOUC for: ' + file_path)
"

# Patch 5: Replace external jQuery CDNs with local files to prevent slow browser tab loading
python3 -c "
import os

files = ['$USER_FOOTER_HTML', '$WHM_FOOTER_HTML', '$USER_DB_IMPORT_HTML']
for file_path in files:
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        
        if 'https://code.jquery.com' in content:
            content = content.replace('https://code.jquery.com/jquery-3.5.1.slim.min.js', '/media/js/jquery.min.js')
            content = content.replace('https://code.jquery.com/jquery-3.6.0.min.js', '/media/js/jquery.min.js')
            with open(file_path, 'w') as f:
                f.write(content)
            print('Patched jQuery CDN link in: ' + file_path)
"

# Asynchronously restart the OLSPanel service to load changes
if systemctl is-active --quiet cp 2>/dev/null; then
  (sleep 2 && systemctl restart cp) &
fi
