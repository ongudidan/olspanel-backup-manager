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

To deploy backups on multiple target servers without committing large binary assets directly to your Git repository (keeping your repository clone size small), you can create releases either in the cloud using GitHub Actions (recommended) or locally using our script.

### Method A: Cloud Release via GitHub Actions (Recommended & Easiest)
This method runs entirely in the cloud on GitHub's servers, requiring **zero local download/upload bandwidth** and **no Personal Access Tokens**.

1. Commit and push the scripts to your GitHub repository:
   ```bash
   git add .
   git commit -m "Add GitHub Actions workflow"
   git push origin main
   ```
2. Go to your repository page on GitHub.
3. Click the **Actions** tab at the top.
4. Select the **Build and Release OLSPanel Backup** workflow on the left.
5. Click the **Run workflow** dropdown on the right:
   * (Optional) Specify the OLSPanel Version (e.g., `3.0.16`). If left blank, it will auto-detect the latest version.
   * (Optional) Adjust the local patching URL if your offline server runs on a different port/IP.
6. Click **Run workflow**. In about 1–2 minutes, a new GitHub Release will automatically be created with the zipped backup asset attached!

---

### Method B: Local Release via Python Script (Alternative)
If you prefer downloading the backup locally first and creating a release from your computer:

1. **Get a GitHub Personal Access Token**:
   Since standard passwords are not supported, generate a **Fine-grained Personal Access Token**:
   * Go to GitHub -> **Settings** -> **Developer settings** -> **Personal access tokens** -> **Fine-grained tokens**.
   * Click **Generate new token**.
   * Under **Repository access**, select **Only select repositories** and choose `olspanel-backup-manager`.
   * Under **Repository permissions**, set **Contents** to **Read and Write**.
   * Click **Generate token** and copy it.

2. **Run the release script**:
   ```bash
   export GITHUB_TOKEN="your_personal_access_token"
   python3 create_release.py
   ```
3. Follow the interactive prompts to confirm details.

---

### Step 2: Download & Install on Target Server
On your fresh target server, run the following commands to automatically resolve, download, and install the **latest** release backup:

```bash
# 1. Resolve and download the latest release asset
ZIP_URL=$(python3 -c "import urllib.request, json; print(json.loads(urllib.request.urlopen(urllib.request.Request('https://api.github.com/repos/ongudidan/olspanel-backup-manager/releases/latest', headers={'User-Agent': 'Mozilla'})).read().decode())['assets'][0]['browser_download_url'])")
wget "$ZIP_URL"

# 2. Extract and run the installer
ZIP_FILE="${ZIP_URL##*/}"
FOLDER="${ZIP_FILE%.zip}"
unzip "$ZIP_FILE"
cd "$FOLDER"
./offline_install.sh
```
