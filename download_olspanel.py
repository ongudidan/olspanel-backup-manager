#!/usr/bin/env python3
import os
import sys
import json
import time
import re
import urllib.request
import urllib.error
from urllib.parse import urljoin
from datetime import datetime

# ==============================================================================
# CONFIGURATION CONSTANTS (Adjust these as needed)
# ==============================================================================
# The default local server address that will replace all remote URLs.
# You can change this value here, or override it at runtime using --local-url.
LOCAL_SERVER_URL = "http://127.0.0.1:8000"

DEFAULT_VERSION = "3.0.16"
GITHUB_OWNER = "osmanfc"
OWPANEL_REPO = "owpanel"
OLSPANEL_REPO = "olspanel"

# Static files on olspanel.com to download
OLSPANEL_STATIC_FILES = [
    # Core system setup ZIP (contains the panel framework code)
    ("https://olspanel.com/panel_setup.zip", "panel_setup.zip"),
    
    # Olsapp plugin setup files
    ("https://olspanel.com/olsapp/install.sh", "olsapp/install.sh"),
    ("https://olspanel.com/olsapp/olsapp.zip", "olsapp/olsapp.zip"),
    ("https://olspanel.com/olsapp/conf_for_bin.ph", "olsapp/conf_for_bin.ph"),
    ("https://olspanel.com/olsapp/softpanel_for_bin.ph", "olsapp/softpanel_for_bin.ph"),
    
    # Installer helper scripts
    ("https://olspanel.com/install.sh", "install.sh"),
    ("https://olspanel.com/extra/re_config.sh", "extra/re_config.sh"),
    ("https://olspanel.com/extra/setup_missing_ssl_file.sh", "extra/setup_missing_ssl_file.sh"),
    ("https://olspanel.com/extra/dovecot/re_conf.sh", "extra/dovecot/re_conf.sh"),
    ("https://olspanel.com/extra/dovecot/dovecot.conf", "extra/dovecot/dovecot.conf"),
    ("https://olspanel.com/extra/swap.sh", "extra/swap.sh"),
    ("https://olspanel.com/extra/database_update.sh", "extra/database_update.sh"),
    ("https://olspanel.com/extra/olspanel.sh", "extra/olspanel.sh"),
    ("https://olspanel.com/extra/ufw_int.sh", "extra/ufw_int.sh"),
    ("https://olspanel.com/extra/install_php_cgi.sh", "extra/install_php_cgi.sh"),
    ("https://olspanel.com/extra/install_cp_plugin", "extra/install_cp_plugin"),
    ("https://olspanel.com/extra/olspanel", "extra/olspanel"),
    
    # Pre-compiled x86_64 binaries & libraries
    ("https://olspanel.com/extra/openssl_lib/libcrypto.so.3", "extra/openssl_lib/libcrypto.so.3"),
    ("https://olspanel.com/extra/openssl_lib/libssl.so.3", "extra/openssl_lib/libssl.so.3"),
    ("https://olspanel.com/extra/olspanelcp", "extra/olspanelcp"),
    
    # Pre-compiled ARM binaries & libraries
    ("https://olspanel.com/extra/openssl_lib/arm/libcrypto.so.3", "extra/openssl_lib/arm/libcrypto.so.3"),
    ("https://olspanel.com/extra/openssl_lib/arm/libssl.so.3", "extra/openssl_lib/arm/libssl.so.3"),
    ("https://olspanel.com/extra/arm/olspanelcp", "extra/arm/olspanelcp"),
    
    # Zipped Plugins
    ("https://olspanel.com/plugin/roundcube.zip", "plugin/roundcube.zip"),
    ("https://olspanel.com/plugin/rainloop.zip", "plugin/rainloop.zip"),
    ("https://olspanel.com/plugin/phpmyadmin.zip", "plugin/phpmyadmin.zip"),
    ("https://olspanel.com/plugin/ufw.zip", "plugin/ufw.zip"),
    ("https://olspanel.com/plugin/config_ufw.zip", "plugin/config_ufw.zip"),
    ("https://olspanel.com/plugin/terminal.zip", "plugin/terminal.zip"),
    ("https://olspanel.com/plugin/terminal_module.zip", "plugin/terminal_module.zip"),
    ("https://olspanel.com/plugin/git_deploy.zip", "plugin/git_deploy.zip"),
    
    # CentOS Repository configurations
    ("https://olspanel.com/repo-files/centos-auth-43.repo", "repo-files/centos-auth-43.repo"),
    
    # Pre-compiled PHP RPM / DEB files
    ("https://olspanel.com/repo-files/centos-php82-cgi/php8.2-8.2.0-1.el9.x86_64.rpm", "repo-files/centos-php82-cgi/php8.2-8.2.0-1.el9.x86_64.rpm"),
    ("https://olspanel.com/repo-files/centos-php83-cgi/php8.3-8.3.0-1.el9.x86_64.rpm", "repo-files/centos-php83-cgi/php8.3-8.3.0-1.el9.x86_64.rpm"),
    ("https://olspanel.com/repo-files/centos-php82-cgi/php8.2-8.2.0-1.el8.x86_64.rpm", "repo-files/centos-php82-cgi/php8.2-8.2.0-1.el8.x86_64.rpm"),
    ("https://olspanel.com/repo-files/ubunto-20-php82-cgi/php8.2_8.2.0-1_amd64.deb", "repo-files/ubunto-20-php82-cgi/php8.2_8.2.0-1_amd64.deb"),
]

# Fallback file lists for GitHub repositories if API is unavailable or rate-limited
FALLBACK_GITHUB_FILES = [
    "Centos/panel.sh",
    "Centos/panelx.sh",
    "Debian/panel.sh",
    "Debian/xpanel.sh",
    "README.md",
    "Ubuntu/panel.sh",
    "Ubuntu/panel_22.sh",
    "Ubuntu/xpanel.sh",
    "install.sh",
    "install_c",
    "item/install",
    "item/panel",
    "reqcentos.txt",
    "requirements.txt",
    "screenshort/Screenshot 2025-02-03 160519.png",
    "screenshort/Screenshot 2025-02-03 160618.png",
    "screenshort/Screenshot 2025-02-03 160649.png",
    "screenshort/Screenshot 2025-02-03 160711.png",
    "screenshort/h.png",
    "screenshort/user-home.png",
    "screenshort/user.png",
    "screenshort/whm.png",
    "ub24req.txt"
]

def request_json(url, headers=None, retries=3):
    """Sends a request to retrieve JSON data with retry logic and redirect handling."""
    if headers is None:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 307, 308):
                new_url = e.headers.get("Location")
                if new_url:
                    return request_json(new_url, headers, retries)
            print(f"  [JSON Error] HTTP error {e.code} for URL {url} on attempt {attempt}/{retries}")
        except Exception as e:
            print(f"  [JSON Error] Failed to fetch {url} on attempt {attempt}/{retries}: {e}")
        
        if attempt < retries:
            time.sleep(2)
    return None

def download_file(url, dest_path, retries=4, timeout=45):
    """Downloads a file to a destination path, displaying a formatted progress bar."""
    url = url.replace(" ", "%20")
    dir_name = os.path.dirname(dest_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    temp_dest = dest_path + ".tmp"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                total_size = int(response.info().get('Content-Length', 0))
                bytes_downloaded = 0
                block_size = 65536
                
                with open(temp_dest, 'wb') as f:
                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        f.write(buffer)
                        bytes_downloaded += len(buffer)
                        if total_size > 0:
                            percent = min(100, int(bytes_downloaded * 100 / total_size))
                            bar_len = 25
                            filled_len = int(bar_len * percent / 100)
                            bar = '█' * filled_len + '-' * (bar_len - filled_len)
                            if total_size > 1024 * 1024:
                                size_str = f"{bytes_downloaded / (1024*1024):.1f}MB/{total_size / (1024*1024):.1f}MB"
                            else:
                                size_str = f"{bytes_downloaded / 1024:.1f}KB/{total_size / 1024:.1f}KB"
                            sys.stdout.write(f"\r  [{bar}] {percent}% ({size_str})")
                            sys.stdout.flush()
                        else:
                            sys.stdout.write(f"\r  Downloaded {bytes_downloaded / 1024:.1f} KB")
                            sys.stdout.flush()
                
                if os.path.exists(temp_dest):
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    os.rename(temp_dest, dest_path)
                sys.stdout.write("\r" + " " * 80 + "\r  ✓ Downloaded successfully.\n")
                sys.stdout.flush()
                return True
        except Exception as e:
            if os.path.exists(temp_dest):
                os.remove(temp_dest)
            sys.stdout.write(f"\r  [Error] Attempt {attempt}/{retries} failed to download {url}: {e}\n")
            sys.stdout.flush()
            if attempt < retries:
                time.sleep(3 * attempt)
    return False

def get_github_files(owner, repo):
    """Uses GitHub API to dynamically retrieve all blobs/files from the main branch."""
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
    print(f"🤖 Querying GitHub repository index for '{owner}/{repo}'...")
    data = request_json(url)
    
    if data and "tree" in data:
        files = [item["path"] for item in data["tree"] if item["type"] == "blob"]
        print(f"  ✓ Discovered {len(files)} files dynamically using GitHub API.")
        return files
    else:
        print(f"  ⚠️ GitHub API rate limit or query failed. Falling back to default list.")
        return FALLBACK_GITHUB_FILES

def download_github_repo(owner, repo, dest_dir, dry_run=False):
    """Downloads all repository files from raw.githubusercontent.com."""
    files = get_github_files(owner, repo)
    base_raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/"
    
    print(f"📦 Downloading repository '{repo}' content...")
    success_count = 0
    fail_count = 0
    
    for index, file_path in enumerate(files, 1):
        url = urljoin(base_raw_url, file_path)
        local_path = os.path.join(dest_dir, file_path)
        print(f"({index}/{len(files)}) {file_path}")
        
        if dry_run:
            print(f"  [Dry-run] Would download from {url}")
            success_count += 1
            continue
            
        if download_file(url, local_path):
            success_count += 1
        else:
            fail_count += 1
            
    print(f"🏁 Finished '{repo}' download. Success: {success_count}, Failed: {fail_count}")
    return fail_count == 0

def parse_and_download_ubuntu22_packages(dest_dir, dry_run=False):
    """Downloads the Packages index file from SURY-compatible Ubuntu 22 php82-repo, parses it, and downloads all referenced .deb files."""
    packages_url = "https://olspanel.com/repo-files/ubunto-22-php82-cgi/php82-repo/Packages"
    local_packages_path = os.path.join(dest_dir, "repo-files/ubunto-22-php82-cgi/php82-repo/Packages")
    
    print("📋 Retrieving Ubuntu 22 php82-repo Packages index...")
    if not dry_run:
        if not download_file(packages_url, local_packages_path):
            print("  ❌ Failed to download packages index list! Skipping package parsing.")
            return False
    else:
        print(f"  [Dry-run] Would download packages list from {packages_url}")
        return True

    # Read and parse Packages file
    with open(local_packages_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    deb_filenames = re.findall(r"^Filename:\s*(.+)$", content, re.MULTILINE)
    print(f"  ✓ Parsed Packages file and found {len(deb_filenames)} package files to download.")
    
    base_deb_url = "https://olspanel.com/repo-files/ubunto-22-php82-cgi/php82-repo/"
    success_count = 0
    fail_count = 0
    
    for index, filename in enumerate(deb_filenames, 1):
        clean_filename = filename.lstrip("./")
        url = urljoin(base_deb_url, clean_filename)
        local_path = os.path.join(dest_dir, "repo-files/ubunto-22-php82-cgi/php82-repo", clean_filename)
        
        print(f"({index}/{len(deb_filenames)}) Package: {clean_filename}")
        if dry_run:
            print(f"  [Dry-run] Would download from {url}")
            success_count += 1
            continue
            
        if download_file(url, local_path):
            success_count += 1
        else:
            fail_count += 1
            
    print(f"🏁 Finished packages download. Success: {success_count}, Failed: {fail_count}")
    return fail_count == 0

# ==============================================================================
# OFFLINE PATCHING LOGIC
# ==============================================================================
def patch_file(filepath, local_url):
    """Replaces remote domains with the local webserver URL and removes query string parameters from URLs."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        
        # 1. Replace raw github owpanel URLs: https://raw.githubusercontent.com/osmanfc/owpanel/main/
        content = re.sub(
            r'https://raw\.githubusercontent\.com/osmanfc/owpanel/main/([^?\s"\']*)(\?([^\s"\'\(\)]+|\([^)]*\))*)?',
            rf'{local_url}/repo_owpanel/\1',
            content
        )
        
        # 2. Replace raw github olspanel URLs: https://raw.githubusercontent.com/osmanfc/olspanel/main/
        content = re.sub(
            r'https://raw\.githubusercontent\.com/osmanfc/olspanel/main/([^?\s"\']*)(\?([^\s"\'\(\)]+|\([^)]*\))*)?',
            rf'{local_url}/repo_olspanel/\1',
            content
        )
        
        # 3. Replace olspanel.com domain links
        content = re.sub(
            r'https://olspanel\.com/([^?\s"\']*)(\?([^\s"\'\(\)]+|\([^)]*\))*)?',
            rf'{local_url}/\1',
            content
        )
        
        # 4. Patch installer credentials to support running on top of an old installation
        if filepath.endswith('.sh'):
            # Replace root password generation to reuse existing one if available
            target1 = 'PASSWORD=$(generate_mariadb_password)  # Change 16 to your desired password length'
            replacement1 = r'''if [ -f "/usr/local/olspanel/mypanel/etc/mysqlPassword" ]; then
    PASSWORD=$(cat "/usr/local/olspanel/mypanel/etc/mysqlPassword")
    echo "Found existing MariaDB root password."
else
    PASSWORD=$(generate_mariadb_password)  # Change 16 to your desired password length
    echo "Generated new MariaDB root password."
fi'''
            content = content.replace(target1, replacement1)

            # Replace panel db user password generation to reuse existing one if available
            target2 = r'''    # Generate a random password for the new user
    local DB_PASSWORD=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 16)
    echo -n "${DB_PASSWORD}" > /root/db_credentials_panel.txt'''
            replacement2 = r'''    # Generate a random password for the new user or load existing
    local DB_PASSWORD=""
    if [ -f "/usr/local/olspanel/mypanel/etc/dbPassword" ]; then
        DB_PASSWORD=$(cat "/usr/local/olspanel/mypanel/etc/dbPassword")
        echo "Found existing database password."
    else
        DB_PASSWORD=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 16)
        mkdir -p "/usr/local/olspanel/mypanel/etc"
        echo -n "${DB_PASSWORD}" > "/usr/local/olspanel/mypanel/etc/dbPassword"
        chmod 600 "/usr/local/olspanel/mypanel/etc/dbPassword"
        echo "Generated new database password."
    fi
    echo -n "${DB_PASSWORD}" > /root/db_credentials_panel.txt'''
            content = content.replace(target2, replacement2)

            # Inject ALTER USER privilege adjustment for database user password updates
            target3 = r'''CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';'''
            replacement3 = r'''CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
ALTER USER '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';'''
            content = content.replace(target3, replacement3)

            # Inject database tables import check to prevent overwriting existing data
            target4 = r'''    echo "Importing database from '$DUMP_FILE' into '$DB_NAME'..."'''
            replacement4 = r'''    # Check if database already has tables to avoid overwriting existing data
    if mysql -u root -p"${ROOT_PASSWORD}" -e "USE \`$DB_NAME\`; SHOW TABLES;" 2>/dev/null | grep -q "[a-zA-Z0-9]"; then
        echo "Database '$DB_NAME' already has tables. Skipping import to preserve existing data."
        return 0
    fi

    echo "Importing database from '$DUMP_FILE' into '$DB_NAME'..."'''
            content = content.replace(target4, replacement4)

            # Patch unzip_and_move to safely copy locally and avoid loopback download/nesting errors
            if os.path.basename(filepath) in ('panel.sh', 'panel_22.sh', 'xpanel.sh'):
                target_unzip = r'''unzip_and_move() {

    wget -O /root/item/panel_setup.zip "http://127.0.0.1:8000/panel_setup.zip"
    local zip_file="/root/item/panel_setup.zip"
    local extract_dir="/root/item/cp"
    local target_dir="/usr/local/olspanel"

    # Ensure the zip file exists
    if [ ! -f "$zip_file" ]; then
        echo "Zip file '$zip_file' does not exist. Exiting."
        return 1
    fi

    # Ensure the target directory exists, create it if it doesn't
    if [ ! -d "$target_dir" ]; then
        echo "Target directory '$target_dir' does not exist. Creating it."
        mkdir -p "$target_dir"
    fi

    # Create the extraction directory if it doesn't exist
    if [ ! -d "$extract_dir" ]; then
        echo "Creating extraction directory: $extract_dir"
        mkdir -p "$extract_dir"
    fi

    # Unzip the file into the extraction directory
    echo "Unzipping '$zip_file' to '$extract_dir'..."
    unzip -o "$zip_file" -d "$extract_dir"
    if [ $? -ne 0 ]; then
        echo "Failed to unzip '$zip_file'. Exiting."
        return 1
    fi

    # Move all extracted files to the target directory
    echo "Moving contents of '$extract_dir' to '$target_dir'..."
    mv "$extract_dir"/* "$target_dir"

    echo "Unzipping and moving completed successfully."
}'''

                replacement_unzip = r'''unzip_and_move() {
    local zip_file="/root/item/panel_setup.zip"
    local extract_dir="/root/item/cp"
    local target_dir="/usr/local/olspanel"

    mkdir -p /root/item

    # Prefer local copy if available to prevent loopback download failures
    if [ -f "./panel_setup.zip" ]; then
        echo "✓ Found local panel_setup.zip, copying directly..."
        cp "./panel_setup.zip" "$zip_file"
    elif [ -f "../panel_setup.zip" ]; then
        echo "✓ Found local panel_setup.zip in parent directory, copying directly..."
        cp "../panel_setup.zip" "$zip_file"
    else
        echo "📡 Downloading panel_setup.zip from local webserver..."
        wget -O "$zip_file" "http://127.0.0.1:8000/panel_setup.zip"
    fi

    # Ensure the zip file exists
    if [ ! -f "$zip_file" ]; then
        echo "❌ Error: Zip file '$zip_file' does not exist."
        return 1
    fi

    # Ensure the target directory exists, create it if it doesn't
    mkdir -p "$target_dir"

    # Create the extraction directory if it doesn't exist
    mkdir -p "$extract_dir"

    # Unzip the file into the extraction directory
    echo "Unzipping '$zip_file' to '$extract_dir'..."
    unzip -o "$zip_file" -d "$extract_dir"
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to unzip '$zip_file'."
        return 1
    fi

    # Move all extracted files to the target directory merging folders safely
    echo "Moving contents of '$extract_dir' to '$target_dir'..."
    cp -r "$extract_dir"/* "$target_dir"/
    rm -rf "$extract_dir"

    echo "Unzipping and moving completed successfully."
}'''
                content = content.replace(target_unzip, replacement_unzip)

                # Ensure exit on error if unzip_and_move fails
                target_call = r'''remove_files_in_html_folder
unzip_and_move
setup_cp_service_with_port'''
                replacement_call = r'''remove_files_in_html_folder
unzip_and_move
if [ $? -ne 0 ]; then
    echo "❌ Error: unzip_and_move failed! Core panel files were not extracted. Aborting install."
    exit 1
fi
setup_cp_service_with_port'''
                content = content.replace(target_call, replacement_call)
            
        # 5. Patch install_cp_plugin to resolve relative paths
        if os.path.basename(filepath) == 'install_cp_plugin':
            target5 = 'PLUGIN_FILE="$1"'
            replacement5 = r'''PLUGIN_FILE="$1"
# Resolve relative paths to absolute paths before we change directories
if [[ ! "$PLUGIN_FILE" =~ ^https?:// ]] && [[ ! "$PLUGIN_FILE" =~ ^/ ]]; then
    PLUGIN_FILE="$(pwd)/$PLUGIN_FILE"
fi'''
            content = content.replace(target5, replacement5)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"  [Error] Failed to patch {filepath}: {e}")
    return False

def patch_directory_for_local(target_dir, local_url):
    """Recursively patches all executable and script files in the backup directory."""
    patched_files = []
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.sh') or file in ('install_cp_plugin', 'olspanel'):
                filepath = os.path.join(root, file)
                if patch_file(filepath, local_url):
                    rel_path = os.path.relpath(filepath, target_dir)
                    patched_files.append(rel_path)
    return patched_files

def get_latest_version_from_site():
    """Scrapes the latest version of OLSPanel from the official website."""
    url = "https://olspanel.com"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
            match = re.search(r'version\s*\(?([0-9.]+)\)?', html, re.IGNORECASE)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"  [Scraper Error] Could not fetch version from homepage: {e}")
    return None

# ==============================================================================
# MAIN ROUTINE
# ==============================================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="OLSPanel Backup Tool - Download all files locally and patch them for offline use.")
    parser.add_argument("--dest", type=str, default="", help="Destination directory name. If empty, a timestamped folder name will be used.")
    parser.add_argument("--local-url", type=str, default=LOCAL_SERVER_URL, help=f"The URL of your local server used for offline patching (default: {LOCAL_SERVER_URL})")
    parser.add_argument("--dry-run", action="store_true", help="Print download file plan without performing downloads or patching.")
    args = parser.parse_args()
    
    print("🤖 Checking official website for the latest version...")
    scraped_version = get_latest_version_from_site()
    version = scraped_version if scraped_version else DEFAULT_VERSION
    if scraped_version:
        print(f"  ✓ Automatically detected latest version: {version}")
    else:
        print(f"  ⚠️ Could not detect version automatically. Using default fallback: {version}")
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_folder = args.dest if args.dest else f"olspanel_backup_v{version}_{timestamp}"
    dest_path = os.path.abspath(dest_folder)
    local_url = args.local_url.rstrip('/')
    
    print("=" * 70)
    print(f"🌟 OLSPanel Unified Downloader & Offline Patcher 🌟")
    print(f"Destination     : {dest_path}")
    print(f"Local Server URL: {local_url}")
    if args.dry_run:
        print("🔧 RUNNING IN DRY-RUN MODE (No files will be modified)")
    print("=" * 70)
    
    # 1. Download GitHub repository files
    print("\n--- [STEP 1: Downloading GitHub Repositories] ---")
    owpanel_dest = os.path.join(dest_path, "repo_owpanel")
    download_github_repo(GITHUB_OWNER, OWPANEL_REPO, owpanel_dest, dry_run=args.dry_run)
    
    olspanel_dest = os.path.join(dest_path, "repo_olspanel")
    download_github_repo(GITHUB_OWNER, OLSPANEL_REPO, olspanel_dest, dry_run=args.dry_run)
    
    # 2. Download Static Server Files
    print("\n--- [STEP 2: Downloading OLSPanel Web Server Resources] ---")
    static_success = 0
    static_fail = 0
    for idx, (url, relative_path) in enumerate(OLSPANEL_STATIC_FILES, 1):
        local_file_path = os.path.join(dest_path, relative_path)
        print(f"({idx}/{len(OLSPANEL_STATIC_FILES)}) {relative_path}")
        
        # Check if we have a local version of this file in plugins/ to copy instead of downloading
        local_override_path = None
        if relative_path == "plugin/terminal.zip":
            local_override_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugins", "terminal.zip")
        elif relative_path == "plugin/terminal_module.zip":
            local_override_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugins", "terminal_module.zip")
        elif relative_path == "plugin/git_deploy.zip":
            local_override_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugins", "git_deploy.zip")

        if local_override_path and os.path.exists(local_override_path):
            print(f"  ✓ Found local override for {relative_path}. Copying from local plugins...")
            if args.dry_run:
                print(f"  [Dry-run] Would copy local {local_override_path} to {local_file_path}")
                static_success += 1
                continue
            
            dir_name = os.path.dirname(local_file_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            import shutil
            shutil.copy2(local_override_path, local_file_path)
            static_success += 1
            print("  ✓ Copied successfully.")
            continue

        if args.dry_run:
            print(f"  [Dry-run] Would download from {url}")
            static_success += 1
            continue
            
        if download_file(url, local_file_path):
            static_success += 1
        else:
            static_fail += 1
            
    print(f"🏁 Finished web server resources download. Success: {static_success}, Failed: {static_fail}")
    
    # 3. Parse and Download Packages
    print("\n--- [STEP 3: Downloading SURY PHP 8.2 Debian/Ubuntu Packages] ---")
    parse_and_download_ubuntu22_packages(dest_path, dry_run=args.dry_run)
    
    # 4. Patch Files for Offline Installation
    print("\n--- [STEP 4: Patching Files for Offline/Local Installation] ---")
    if not args.dry_run:
        patched = patch_directory_for_local(dest_path, local_url)
        print(f"✓ Patched {len(patched)} script files to redirect installer downloads.")
        for pf in patched:
            print(f"  - {pf}")
            
        # Write offline installer instructions guide
        readme_content = f"""# Offline OLSPanel Installation Guide

This backup has been patched to run entirely using a local web server, ensuring you do not require any connection to the developer's domains (`olspanel.com` or `github.com`).

An automated script `offline_install.sh` has been provided to completely automate this process.

## Automated Installation (Single Command)

### Step 1: Copy Backup to the Target Server
Copy the entire `{os.path.basename(dest_path)}` folder to your fresh target server:
```bash
scp -r {os.path.basename(dest_path)} root@your-server-ip:/root/
```

### Step 2: Run the Automated Installer
On the target server, navigate into the folder and run the automated installer:
```bash
cd /root/{os.path.basename(dest_path)}
./offline_install.sh
```
This script will automatically start the local web server in the background, run the patched installation process, and shut down the server when completed!

---

## Manual Installation (Alternative)

If you prefer to run it manually step-by-step:

1. Start Python's built-in HTTP server in the backup folder on the target server:
   ```bash
   cd /root/{os.path.basename(dest_path)}
   python3 -m http.server 8000
   ```
2. Open another terminal session on the target server and execute the patched installer:
   ```bash
   bash <(curl -fsSL {local_url}/install.sh)
   ```
"""
        readme_path = os.path.join(dest_path, "README_OFFLINE.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        print(f"✓ Generated offline guide: {readme_path}")
        
        # Write offline_install.sh script
        offline_install_content = f"""#!/bin/bash
# OLSPanel Automated Local/Offline Installer

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "🚀 Starting OLSPanel Automated Local Installer..."
echo "=================================================="

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️ Warning: Port 8000 is already in use. Assuming local file server is running."
else
    echo "1. Launching local file server on port 8000 in background..."
    python3 -m http.server 8000 > /dev/null 2>&1 &
    SERVER_PID=$!
    
    # Ensure the server is stopped when this script exits
    cleanup() {{
        echo ""
        echo "🧹 Stopping local file server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null
    }}
    trap cleanup EXIT
    
    # Wait for the local server to start
    sleep 2
fi

echo "2. Executing patched OLSPanel installer..."
chmod +x install.sh
./install.sh

# Automatically install custom terminal plugin if available
if [ -f "/usr/local/bin/install_cp_plugin" ] && [ -f "$SCRIPT_DIR/plugin/terminal.zip" ]; then
    echo "3. Automatically installing OLSPanel Terminal Plugin..."
    /usr/local/bin/install_cp_plugin "$SCRIPT_DIR/plugin/terminal.zip"
fi

# Automatically install custom git deploy plugin if available
if [ -f "/usr/local/bin/install_cp_plugin" ] && [ -f "$SCRIPT_DIR/plugin/git_deploy.zip" ]; then
    echo "4. Automatically installing OLSPanel Git Deploy Plugin..."
    /usr/local/bin/install_cp_plugin "$SCRIPT_DIR/plugin/git_deploy.zip"
fi

echo "=================================================="
echo "🎉 Automated installer script finished!"
echo "=================================================="
"""
        offline_install_path = os.path.join(dest_path, "offline_install.sh")
        with open(offline_install_path, "w", encoding="utf-8") as f:
            f.write(offline_install_content)
        os.chmod(offline_install_path, 0o755)
        print(f"✓ Generated automated local installer wrapper: {offline_install_path}")
    else:
        print("[Dry-run] Would patch all script files in destination to use local URL.")
        
    print("\n" + "=" * 70)
    print("🚀 OLSPanel local backup download and offline patching complete!")
    print(f"Saved to: {dest_path}")
    print("=" * 70)

if __name__ == "__main__":
    main()
