#!/bin/bash

printf "\nOLS Panel is now starting soon please wait...\n\n"

OUTPUT=$(cat /etc/*release)
ARCH=$(uname -m)

if echo "$OUTPUT" | grep -q "Ubuntu 18.04"; then
    SERVER_OS="Ubuntu"
    sudo apt update -qq && sudo apt install -y -qq wget curl
elif echo "$OUTPUT" | grep -q "Ubuntu 20.04"; then
    SERVER_OS="Ubuntu"
    sudo apt update -qq && sudo apt install -y -qq wget curl
elif echo "$OUTPUT" | grep -q "Ubuntu 22.04"; then
    SERVER_OS="Ubuntu"
    sudo apt update -qq && sudo apt install -y -qq wget curl
elif echo "$OUTPUT" | grep -q "Ubuntu 24.04"; then
    SERVER_OS="Ubuntu"
    sudo apt update -qq && sudo apt install -y -qq wget curl
elif echo "$OUTPUT" | grep -q "Debian"; then
    SERVER_OS="Debian"
    sudo apt update -qq && sudo apt install -y -qq wget curl
elif echo "$OUTPUT" | grep -q "AlmaLinux 8"; then
    SERVER_OS="Centos"
    sudo dnf update -y && sudo dnf install -y wget curl
elif echo "$OUTPUT" | grep -q "AlmaLinux 9"; then
    SERVER_OS="Centos"
    sudo dnf update -y && sudo dnf install -y wget curl
elif echo "$OUTPUT" | grep -q "CentOS Linux 8" || echo "$OUTPUT" | grep -q "CentOS Stream 8"; then
    SERVER_OS="Centos"
    sudo dnf update -y && sudo dnf install -y wget curl
elif echo "$OUTPUT" | grep -q "CentOS Stream 9"; then
    SERVER_OS="Centos"
    sudo dnf update -y && sudo dnf install -y wget curl
elif echo "$OUTPUT" | grep -q "Rocky Linux 8"; then
    SERVER_OS="Centos"
    sudo dnf update -y && sudo dnf install -y wget curl
elif echo "$OUTPUT" | grep -q "Rocky Linux 9"; then
    SERVER_OS="Centos"
    sudo dnf update -y && sudo dnf install -y wget curl
else
    printf "\nUnsupported OS.\n\n"
    exit 1
fi

if [[ "$ARCH" == "aarch64" || "$ARCH" == "armv7l" ]]; then
    PANEL_ARCH="arm"
else
    PANEL_ARCH="x86"
fi

if [[ "$SERVER_OS" == "Ubuntu" && "$PANEL_ARCH" == "arm" ]]; then
    PANEL_FILE="panel.sh"
else
    PANEL_FILE="panel.sh"
fi

printf "\nYour OS is %s\n\n" "$SERVER_OS"

wget -O panel.sh "http://127.0.0.1:8000/repo_owpanel/$SERVER_OS/$PANEL_FILE"
wget -O requirements.txt "http://127.0.0.1:8000/repo_owpanel/requirements.txt"

chmod +x panel.sh
sed -i 's/\r$//' panel.sh

./panel.sh