import os
import hashlib
import base58
import multiprocessing
from multiprocessing import Process, Value, Lock
from time import time, sleep
from colorama import init, Fore, Style
from mnemonic import Mnemonic
import bip32utils
import ecdsa
from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv
import requests
from requests.exceptions import RequestException
from faker import Faker

# Initialize colorama
init(autoreset=True)
# Initialize Faker
fake = Faker()
# Load environment variables from .env file
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def generate_seed_phrase(strength=256):
    """Generate a mnemonic seed phrase (12 or 24 words)."""
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=strength)


def seed_phrase_to_private_key(seed_phrase):
    """Convert a seed phrase to a private key."""
    mnemo = Mnemonic("english")
    seed = mnemo.to_seed(seed_phrase)
    bip32_root_key_obj = bip32utils.BIP32Key.fromEntropy(seed)
    bip32_child_key_obj = (
        bip32_root_key_obj.ChildKey(44 + bip32utils.BIP32_HARDEN)  # 44'
        .ChildKey(0 + bip32utils.BIP32_HARDEN)  # 0'
        .ChildKey(0 + bip32utils.BIP32_HARDEN)  # 0'
        .ChildKey(0)
        .ChildKey(0)
    )
    return bip32_child_key_obj.PrivateKey(), bip32_child_key_obj.WalletImportFormat()


def private_key_to_public_key(private_key):
    """Convert a private key to a public key using ECDSA."""
    key = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    return b"\x04" + key.verifying_key.to_string()


def public_key_to_address(public_key):
    """Convert a public key to a Bitcoin address using SHA-256 and RIPEMD-160."""
    sha256 = hashlib.sha256(public_key).digest()
    ripemd160 = hashlib.new("ripemd160")
    ripemd160.update(sha256)
    network_byte = b"\x00"
    network_bitcoin_public_key = network_byte + ripemd160.digest()
    double_sha256 = hashlib.sha256(
        hashlib.sha256(network_bitcoin_public_key).digest()
    ).digest()
    checksum = double_sha256[:4]
    return base58.b58encode(network_bitcoin_public_key + checksum).decode("utf-8")


def save_to_file(seed_phrase, address):
    """Save generated address and details to crypto.txt."""
    with open("crypto.txt", "a") as file:
        file.write(f"Address: {address}\nSeed Phrase: {seed_phrase}\n\n")


def generate_random_user_agent():
    """Generate a random User-Agent string using Faker."""
    return fake.user_agent()


def check_balance(address):
    """Check the balance of a Bitcoin address using an API with a random User-Agent."""
    try:
        user_agent = generate_random_user_agent()  # Generate a random User-Agent

        headers = {"User-Agent": user_agent}

        response = requests.get(
            f"https://blockchain.info/q/addressbalance/{address}", headers=headers
        )

        if response.status_code == 200:
            balance = int(response.text) / 1e8  # Convert from satoshi to BTC
            return balance
        else:
            return 0

    except RequestException as e:
        print(f"Error checking balance: {e}")
        return 0


def send_telegram_message(seed_phrase, address, balance):
    """Send a notification to Telegram about the found match."""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        message = (
            f"🚨 Bitcoin address match found! 🚨\n\n"
            f"Address: {address}\nSeed Phrase: {seed_phrase}\nBalance: {balance} BTC \n Developer: Karan Kumar \n Organization: @CyberZoneAcademy"
        )
        try:
            updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
            updater.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        except Exception as e:
            pass


def worker(counter, found_counter, lock):
    """Generate keys from seed phrases, convert to addresses, and check against the rich list."""
    while True:
        seed_phrase = generate_seed_phrase()
        private_key, wif = seed_phrase_to_private_key(seed_phrase)
        public_key = private_key_to_public_key(private_key)
        address = public_key_to_address(public_key)
        with lock:
            counter.value += 1
            print(
                f"\r{Fore.GREEN}Addresses Generated: {counter.value}{Style.RESET_ALL}",
                end="",
            )
        balance = check_balance(address)
        if balance > 0:
            with lock:
                found_counter.value += 1
            save_to_file(seed_phrase, address)
            send_telegram_message(seed_phrase, address, balance)


def display_performance(counter, found_counter, lock):
    """Display performance metrics periodically."""
    while True:
        with lock:
            key_count = counter.value
            found_count = found_counter.value
        print(
            f"\r{Fore.CYAN}Addresses Generated: {key_count} - Matches Found: {found_count}{Style.RESET_ALL}",
            end="",
        )
        sleep(1)  # Update every second


def main():
    num_workers = multiprocessing.cpu_count()
    counter = Value("i", 0)
    found_counter = Value("i", 0)
    lock = Lock()

    processes = [
        Process(target=worker, args=(counter, found_counter, lock))
        for _ in range(num_workers)
    ]
    monitor = Process(target=display_performance, args=(counter, found_counter, lock))

    for process in processes:
        process.start()
    monitor.start()

    try:
        monitor.join()  # Keep the main thread alive to allow monitoring and workers to run indefinitely
    except KeyboardInterrupt:
        for process in processes:
            process.terminate()
        monitor.terminate()
        for process in processes:
            process.join()
        monitor.join()


if __name__ == "__main__":
    main()
