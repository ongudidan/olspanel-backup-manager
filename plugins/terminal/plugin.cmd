#!/bin/bash

PHP_LIB="/etc/php/8.2"
SO_NAME="ssh2.so"
INI_FILE_PATH="/etc/php/8.2/cgi/php.ini"
HOME_PATH_FILE="/etc/olspanel/base_dir"

# Detect project dir
if [ -f "$HOME_PATH_FILE" ]; then
    PROJECT_DIR="$(cat "$HOME_PATH_FILE")"
else
    PROJECT_DIR="/usr/local/lsws/Example/html/mypanel"
fi

MODULE_DIR="$PROJECT_DIR/modules"

echo "Using project dir: $PROJECT_DIR"

# Ensure directories exist
mkdir -p "$MODULE_DIR"
mkdir -p "$PHP_LIB/modules"

# -------------------------------
# Install ssh2 PHP extension
# -------------------------------
if command -v apt >/dev/null 2>&1; then
    echo "Debian/Ubuntu detected"

    sudo apt update -y
    sudo apt install -y lsof libssh2-1 libssh2-1-dev gcc make autoconf libtool
    sudo apt install -y lsphp82-dev
	sudo apt install -y lsphp82-pear

  

elif command -v dnf >/dev/null 2>&1; then
    echo "RHEL / AlmaLinux / Rocky / Fedora detected"

    sudo dnf install -y epel-release
    sudo dnf install -y lsof libssh2 libssh2-devel gcc make autoconf libtool
    sudo dnf install -y lsphp82-devel
	sudo dnf install -y lsphp82-pear

    

fi

yes '' | /usr/local/lsws/lsphp82/bin/pecl install -f ssh2

# Find ssh2.so automatically
SSH2_SO=$(find /usr/local/lsws/lsphp82/ -name ssh2.so | head -n 1)

if [ -z "$SSH2_SO" ]; then
    echo "❌ ssh2.so not found"
    exit 1
fi

echo "Found: $SSH2_SO"

# Add extension to php.ini only once
if ! grep -q "^extension=$SSH2_SO" "$INI_FILE_PATH"; then
    echo "" >> "$INI_FILE_PATH"
    echo "extension=$SSH2_SO" >> "$INI_FILE_PATH"
    echo "✅ ssh2 extension enabled"
else
    echo "✅ ssh2 already enabled"
fi



# -------------------------------
# Install terminal module
# -------------------------------
echo "Installing terminal module"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/terminal_module.zip" ]; then
    echo "Found local terminal_module.zip. Copying offline..."
    cp "$SCRIPT_DIR/terminal_module.zip" "$MODULE_DIR/terminal.zip"
else
    echo "Downloading terminal module..."
    wget -q -O "$MODULE_DIR/terminal.zip" \
    "https://olspanel.com/plugin/terminal_module.zip?$(date +%s)"
fi

unzip -oq "$MODULE_DIR/terminal.zip" -d "$MODULE_DIR"
rm -f "$MODULE_DIR/terminal.zip"

# -------------------------------
# Configure SSH Local Password Authentication
# -------------------------------
echo "Configuring SSH Local Password Authentication..."
SSHD_CONFIG="/etc/ssh/sshd_config"
if [ -f "$SSHD_CONFIG" ]; then
    if ! grep -q "Match Address 127.0.0.1,::1" "$SSHD_CONFIG"; then
        echo -e "\n# Allow local password authentication for terminal plugin loopback\nMatch Address 127.0.0.1,::1\n    PasswordAuthentication yes" | sudo tee -a "$SSHD_CONFIG" > /dev/null
        echo "✅ SSH local password authentication added"
        
        # Test SSH configuration validity
        if sudo sshd -t; then
            if systemctl is-active --quiet sshd 2>/dev/null; then
                sudo systemctl restart sshd
            elif systemctl is-active --quiet ssh 2>/dev/null; then
                sudo systemctl restart ssh
            fi
            echo "⚡ SSH service restarted"
        else
            echo "❌ SSH config check failed! Reverting..."
            # Remove the last 4 lines we added
            sudo sed -i '/# Allow local password authentication for terminal plugin loopback/,+3d' "$SSHD_CONFIG"
        fi
    else
        echo "✅ SSH local password authentication already configured"
    fi
else
    echo "⚠️ Warning: SSH configuration file not found at $SSHD_CONFIG"
fi

echo "✅ Terminal module installed successfully"
sudo systemctl restart cp

