# Offline OLSPanel Installation Guide

This backup has been patched to run entirely using a local web server, ensuring you do not require any connection to the developer's domains (`olspanel.com` or `github.com`).

## Step 1: Transfer Backup to the Target Server
Copy the entire `olspanel_backup_v3.0.16_20260623_122910` folder to your fresh target server.

## Step 2: Start a Local Web Server
On the target server, navigate into the backup folder and start a built-in Python web server to host the installer files locally:
```bash
cd olspanel_backup_v3.0.16_20260623_122910
python3 -m http.server 8000
```
This will host all backup files at `http://127.0.0.1:8000`.

## Step 3: Run the Patched Installer
Open another terminal session on the target server and execute the patched installer:
```bash
# Run the local installer pointing to the local web server
bash <(curl -fsSL http://127.0.0.1:8000/install.sh)
```
The installer will pull all scripts, compiled binaries, packages, and database templates from your local server instead of making remote calls!
