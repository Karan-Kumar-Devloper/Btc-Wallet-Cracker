# Btc-Wallet-Cracker

Welcome to the **Btc-Wallet-Cracker** repository. This project provides a tool for Bitcoin wallet cracking.

## Prerequisites

Before you start, ensure you have the following installed on your machine:

- **Python 3.x**
- **pip** (Python package installer)
- **Git** (for cloning the repository)

## Installation Guide for Linux

### 1. Clone the Repository

Open a terminal and clone the repository to your local machine:

```sh
git clone https://github.com/Karan-Kumar-Devloper/Btc-Wallet-Cracker.git
```

Navigate to the project directory:

```sh
cd Btc-Wallet-Cracker
```

### 2. Run the `setup.sh` Script

The `setup.sh` script automates the installation of necessary dependencies and sets up the environment.

1. **Ensure the script is executable**:

   ```sh
   chmod +x setup.sh
   ```

2. **Run the script**:

   ```sh
   ./setup.sh
   ```

## `setup.sh` Script Overview

The `setup.sh` script performs the following tasks:

1. **Checks if Python and pip are installed**. If not, it installs them.
2. **Updates pip** to the latest version.
3. **Installs required Python modules**: `colorama`, `mnemonic`, `bip32utils`, `ecdsa`, `python-telegram-bot`, `python-dotenv`, `requests`, and `faker`.
4. **Runs the provided Python script** (`btc-wallet-cracker.py`).
5. **Prints developer and organization information**.

### Notes

- Ensure `setup.sh` and any required Python scripts are in the same directory.
- Replace `btc-wallet-cracker.py` in the `setup.sh` script with the name of the actual Python script you want to run.

## Developer and Organization

- **Developer:** Karan Kumar
- **Organization:** Cyber Zone Academy

For any questions or issues, please contact the developer or refer to the repository documentation.

## License

This project is licensed under the [MIT License](LICENSE).


