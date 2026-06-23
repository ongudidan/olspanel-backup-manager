# 🚀 olspanel-backup-manager

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

### Step 1: Copy Backup to the Target Server
Transfer the entire downloaded folder (e.g., `olspanel_v3.0.16`) to the fresh server. You can do this using `scp` or `rsync`:
```bash
scp -r olspanel_v3.0.16 root@your-server-ip:/root/
```

### Step 2: Run the Automated Installer
On the target server, navigate into the backup folder and execute the automated installer script:
```bash
cd /root/olspanel_v3.0.16
./offline_install.sh
```
*Note: This single script automatically boots Python's built-in file server in the background on port 8000, triggers the installation pointing to it, and cleanly shuts down the file server when the installation completes.*

---


## 📦 Creating and Deploying Releases via GitHub

To deploy backups on multiple target servers without committing large binary assets directly to your Git repository (keeping your repository clone size small), you can use the automated release helper script [create_release.py](file:///home/ongudidan/Projects/TOOLS/OLSPanel%20Full/create_release.py).

This script automatically zips your backup folder, creates a GitHub Release, and uploads the compressed archive as a release asset in one step.

### Step 1: Run the Release Script
1. **Set your GitHub Token** (Optional, or the script will prompt you for it):
   ```bash
   export GITHUB_TOKEN="your_personal_access_token"
   ```
2. **Run the script**:
   ```bash
   python3 create_release.py
   ```
3. Follow the interactive prompts to select the backup folder, confirm details, and optionally delete the temporary local `.zip` file after a successful upload.

### Step 2: Download & Install on Target Server
On your fresh target server, download only the required release archive directly (no repository cloning needed):
```bash
# Download the single release zip file (replace username/repo and version as needed)
wget https://github.com/ongudidan/olspanel-backup-manager/releases/download/v3.0.16/olspanel_v3.0.16.zip

# Unzip and run the automated installer
unzip olspanel_v3.0.16.zip
cd olspanel_v3.0.16/
./offline_install.sh
```
