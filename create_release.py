#!/usr/bin/env python3
import os
import sys
import json
import zipfile
import subprocess
import urllib.request
import urllib.error
from urllib.parse import urlencode

def get_git_remote():
    """Auto-detects the GitHub repository owner and name from git config."""
    try:
        url = subprocess.check_output(["git", "remote", "get-url", "origin"], stderr=subprocess.DEVNULL).decode().strip()
        if url.endswith(".git"):
            url = url[:-4]
        if "github.com" in url:
            parts = url.split("github.com")[-1].strip(":/").split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
    except Exception:
        pass
    return None, None

def zip_directory(source_dir, output_zip_path):
    """Zips the contents of a directory with progress indicators."""
    print(f"📦 Compressing '{source_dir}' into '{output_zip_path}'...")
    
    # Count files to show progress
    file_paths = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            file_paths.append(os.path.join(root, file))
            
    total_files = len(file_paths)
    if total_files == 0:
        print("  ❌ No files found in the directory!")
        return False

    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for idx, file_path in enumerate(file_paths, 1):
            arcname = os.path.relpath(file_path, os.path.dirname(source_dir))
            zipf.write(file_path, arcname)
            if idx % max(1, total_files // 10) == 0 or idx == total_files:
                percent = int(idx * 100 / total_files)
                sys.stdout.write(f"\r  Compressing: [{percent}%] {idx}/{total_files} files packed")
                sys.stdout.flush()
                
    sys.stdout.write("\n  ✓ Compression complete!\n")
    sys.stdout.flush()
    return True

def make_github_request(url, token, data=None, method="GET", content_type="application/json"):
    """Helper to perform authorized GitHub API requests using standard library urllib."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-API-Version": "2022-11-28",
        "User-Agent": "OLSPanel-Backup-Release-Manager"
    }
    if content_type:
        headers["Content-Type"] = content_type

    req_data = None
    if data is not None:
        if isinstance(data, (dict, list)):
            req_data = json.dumps(data).encode("utf-8")
        else:
            req_data = data  # raw bytes

    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read()
            if res_body:
                return json.loads(res_body.decode("utf-8")), response.status
            return {}, response.status
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        print(f"\n  ❌ HTTP Error {e.code}: {e.reason}")
        try:
            err_json = json.loads(err_msg)
            print(f"  GitHub API Message: {err_json.get('message', 'No message details')}")
            if "errors" in err_json:
                for error in err_json["errors"]:
                    print(f"    - {error}")
        except Exception:
            print(f"  Response: {err_msg}")
        return None, e.code
    except Exception as e:
        print(f"\n  ❌ Network/System Error: {e}")
        return None, 500

def main():
    print("=" * 70)
    print("🚀 OLSPanel GitHub Release Creator & Asset Uploader")
    print("=" * 70)
    
    # 1. Resolve owner and repository
    owner, repo = get_git_remote()
    if not owner or not repo:
        print("⚠️  Could not auto-detect GitHub repository from local git config.")
        owner = input("Enter GitHub Username/Owner (e.g. ongudidan): ").strip()
        repo = input("Enter GitHub Repository Name (e.g. olspanel-backup-manager): ").strip()
    else:
        print(f"✓ Detected Repository: {owner}/{repo}")
        
    if not owner or not repo:
        print("❌ Owner and Repository are required. Exiting.")
        sys.exit(1)

    # 2. Locate backup directory
    all_dirs = [d for d in os.listdir(".") if os.path.isdir(d) and "olspanel" in d.lower() and d != ".git"]
    if not all_dirs:
        print("❌ No backup directories (containing 'olspanel') found in this folder.")
        sys.exit(1)
        
    print("\nAvailable Backup Directories:")
    for idx, d in enumerate(all_dirs, 1):
        print(f"  [{idx}] {d}")
        
    choice = 1
    if len(all_dirs) > 1:
        try:
            choice_str = input(f"Select backup directory to release (default [1]): ").strip()
            if choice_str:
                choice = int(choice_str)
        except ValueError:
            print("Invalid choice. Using option [1].")
            
    if choice < 1 or choice > len(all_dirs):
        print("Selection out of range. Using option [1].")
        choice = 1
        
    target_dir = all_dirs[choice - 1]
    print(f"Selected: {target_dir}")
    
    # Auto-extract version
    version = "3.0.16"
    ver_match = re.search(r"v([0-9.]+)", target_dir)
    if ver_match:
        version = ver_match.group(1)
        
    tag_name = f"v{version}"
    release_title = f"Version {version}"
    release_notes = f"Clean offline-patched local backup of OLSPanel {version}."
    
    # Confirm release details
    print(f"\nRelease Details:")
    print(f"  Tag Name     : {tag_name}")
    print(f"  Release Title: {release_title}")
    
    # Ask if they want to override tag/title
    override = input("Do you want to override the Tag Name or Title? (y/N): ").strip().lower()
    if override == "y":
        tag_name = input(f"Enter Tag Name (default: {tag_name}): ").strip() or tag_name
        release_title = input(f"Enter Release Title (default: {release_title}): ").strip() or release_title
        release_notes = input(f"Enter Release Notes (default: {release_notes}): ").strip() or release_notes

    # 3. Retrieve GitHub Token
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        print("\n🔑 A GitHub Personal Access Token (PAT) is required to authenticate.")
        print("You can generate one here: https://github.com/settings/tokens")
        print("Ensure the token has 'repo' scopes enabled.")
        token = input("Enter your GitHub PAT: ").strip()
        
    if not token:
        print("❌ GitHub Personal Access Token is required to authenticate. Exiting.")
        sys.exit(1)

    # 4. Zip the directory
    zip_filename = f"{target_dir}.zip"
    zip_filepath = os.path.abspath(zip_filename)
    
    if os.path.exists(zip_filepath):
        reuse = input(f"\nArchive '{zip_filename}' already exists. Re-create it? (Y/n): ").strip().lower()
        if reuse != "n":
            if not zip_directory(target_dir, zip_filepath):
                sys.exit(1)
    else:
        if not zip_directory(target_dir, zip_filepath):
            sys.exit(1)
            
    # Calculate file size
    zip_size_mb = os.path.getsize(zip_filepath) / (1024 * 1024)
    print(f"✓ Archive ready: {zip_filename} ({zip_size_mb:.2f} MB)")

    # 5. Create GitHub Release
    print(f"\n📡 Contacting GitHub API to create release '{tag_name}'...")
    create_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    release_payload = {
        "tag_name": tag_name,
        "name": release_title,
        "body": release_notes,
        "draft": False,
        "prerelease": False
    }
    
    res, status = make_github_request(create_url, token, data=release_payload, method="POST")
    if status == 422:
        # Release already exists, fetch it to upload to it
        print("  ⚠️ Release already exists. Fetching existing release details...")
        get_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag_name}"
        res, status = make_github_request(get_url, token, method="GET")
        
    if not res or "upload_url" not in res:
        print("❌ Failed to resolve GitHub release details. Exiting.")
        sys.exit(1)
        
    upload_url_template = res["upload_url"]
    html_url = res["html_url"]
    print(f"✓ Release resolved: {html_url}")
    
    # 6. Upload Asset
    clean_upload_url = upload_url_template.split("{")[0]
    upload_url = f"{clean_upload_url}?name={zip_filename}"
    
    print(f"\n⬆️  Uploading '{zip_filename}' to GitHub Releases...")
    print("  (This may take a moment depending on your network connection. Please wait...)")
    
    # Read binary data
    with open(zip_filepath, "rb") as f:
        binary_data = f.read()
        
    upload_res, upload_status = make_github_request(
        upload_url, 
        token, 
        data=binary_data, 
        method="POST", 
        content_type="application/zip"
    )
    
    if upload_status in (200, 201):
        print(f"\n🎉 Release created and asset uploaded successfully!")
        print(f"🔗 View Release: {html_url}")
        print(f"⬇️ Direct Download Link:")
        print(f"  https://github.com/{owner}/{repo}/releases/download/{tag_name}/{zip_filename}")
        
        # Optionally delete local zip file
        clean = input(f"\nClean up local zip file '{zip_filename}'? (y/N): ").strip().lower()
        if clean == "y":
            os.remove(zip_filepath)
            print("✓ Local zip file removed.")
    else:
        print(f"\n❌ Failed to upload asset. Status Code: {upload_status}")
        print("Please check the error output above.")

import re
if __name__ == "__main__":
    main()
