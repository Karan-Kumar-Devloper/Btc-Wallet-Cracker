#!/bin/bash

# Load colorama for colored output
pip install colorama

# Import colorama and set up colors
python - <<EOF
from colorama import init, Fore
init(autoreset=True)
print(Fore.CYAN + "Checking if Python is installed...")
EOF

# Print developer and organization information
python - <<EOF
from colorama import Fore
print(Fore.YELLOW + "Developer: Karan Kumar")
print(Fore.YELLOW + "Organization: Cyber Zone Academy")
EOF

# Check if Python is installed
if command -v python3 >/dev/null 2>&1; then
    echo -e "\033[32mPython is already installed."
else
    echo -e "\033[31mPython is not installed. Installing Python..."
    # Install Python (Debian-based systems example; adjust as necessary for your OS)
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip
fi

# Check if pip is installed
if command -v pip3 >/dev/null 2>&1; then
    echo -e "\033[32mpip is already installed."
else
    echo -e "\033[31mpip is not installed. Installing pip..."
    sudo apt-get install -y python3-pip
fi

# Update pip to the latest version
echo -e "\033[34mUpdating pip to the latest version..."
pip install --upgrade pip

# Install required Python modules
echo -e "\033[34mInstalling required Python modules..."
pip install colorama mnemonic bip32utils ecdsa python-telegram-bot python-dotenv requests faker

# Print success message
python - <<EOF
from colorama import Fore
print(Fore.GREEN + "All modules have been installed successfully.")
EOF

# Run the provided Python script
echo -e "\033[34mRunning the provided Python script..."
python3 btc-wallet-cracker.py

# Print final message
python - <<EOF
from colorama import Fore
print(Fore.GREEN + "The provided Python script has been executed.")
EOF
