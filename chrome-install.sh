#!/bin/bash
# Install Chrome for Selenium on Railway
echo "Installing Chrome for Selenium..."

# Update package list
apt-get update

# Install Chrome dependencies
apt-get install -y wget gnupg2 software-properties-common

# Add Google Chrome repository
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

# Update and install Chrome
apt-get update
apt-get install -y google-chrome-stable

# Verify installation
if command -v google-chrome >/dev/null 2>&1; then
    echo "Chrome installed successfully: $(google-chrome --version)"
else
    echo "Chrome installation failed"
    exit 1
fi

# Set environment variables
export CHROME_BIN=/usr/bin/google-chrome
export CHROME_PATH=/usr/bin/google-chrome

echo "Chrome installation complete!"
