# 🚀 OLSPanel Offline Downloader & Backup Manager

This repository contains tools to completely download, backup, and patch the OLSPanel hosting control panel for standalone, local, or offline installation. By mirroring all repositories, zips, precompiled binaries, and package indexes locally, you can deploy and maintain your own panel independently of the developer's remote servers.

---

## 📥 How to Run the Downloader Script

The downloader script [download_olspanel.py](file:///home/ongudidan/Projects/TOOLS/OLSPanel%20Full/download_olspanel.py) uses only standard Python 3 libraries (no external dependencies required) and automatically handles downloads and offline patching in a single run.

### 1. Basic Download & Patch (Default)
Run the script to automatically scrape the official OLSPanel website for the latest version, download the complete stack, and organize it into a new folder named with the resolved version and a timestamp (e.g. `olspanel_backup_v3.0.16_YYYYMMDD_HHMMSS`):
```bash
python3 download_olspanel.py
```
This will automatically patch the installer files to use the default local address: `http://127.0.0.1:8000`.

### 2. Custom Backup Folder Name
To save the backup files in a specific directory:
```bash
python3 download_olspanel.py --dest olspanel_v3.0.16
```

### 3. Custom Local Web Server URL
If you plan to run your local installer file server on a specific IP address (e.g., `http://192.168.1.100:8000`), you can pass it during download:
```bash
python3 download_olspanel.py --dest olspanel_v3.0.16 --local-url http://192.168.1.100:8000
```
*Note: You can also edit the default `LOCAL_SERVER_URL = "http://127.0.0.1:8000"` variable directly at the top of the `download_olspanel.py` file to set your permanent default.*

### 4. Dry-run Mode
To preview which remote URLs would be fetched and where they would be saved on your disk without performing any actual downloads:
```bash
python3 download_olspanel.py --dry-run
```

---

## 🛠️ Offline / Local Installation Guide

To install the panel on a fresh target server using your local backup without contacting the developer's domains:

### Step 1: Copy Backup to Target Server
Transfer the entire downloaded folder (e.g., `olspanel_v3.0.16`) to the fresh server where you want to install OLSPanel. You can do this using `scp`, `rsync`, or an archive:
```bash
scp -r olspanel_v3.0.16 root@your-server-ip:/root/
```

### Step 2: Start the Local File Server
On the target server, navigate to the backup folder and start Python's built-in HTTP server:
```bash
cd /root/olspanel_v3.0.16
python3 -m http.server 8000
```
This serves all installer files, zips, and package files locally at `http://127.0.0.1:8000`.

### Step 3: Run the Patched Installer
Open another SSH connection to your target server and run the installation command pointing to the local web server:
```bash
bash <(curl -fsSL http://127.0.0.1:8000/install.sh)
```

The installer will perform all its setup routines, pulling scripts, compiled binaries, plugins, database structures, and the custom SURY PHP deb/rpm packages entirely from your local Python server.
# olspanel-backup-manager
