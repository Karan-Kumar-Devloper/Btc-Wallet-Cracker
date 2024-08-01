import asyncio
import os
import hashlib
import base58
import multiprocessing
from multiprocessing import Process, Value, Lock
from time import sleep
from colorama import init, Fore, Style
from mnemonic import Mnemonic
import bip32utils
import ecdsa
from telegram import Bot
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

# Retrieve Telegram credentials from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
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

async def send_telegram_message_async(seed_phrase, address, balance):
    """Send a notification to Telegram about the found match."""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        message = (
            f"🚨 *Bitcoin Address Match Found!* 🚨\n\n"
            f"🔑 *Seed Phrase:* \n`{seed_phrase}`\n\n"
            f"📫 *Address:* \n`{address}`\n\n"
            f"💰 *Balance:* `{balance} BTC`\n\n"
            f"👨‍💻 *Developer:* Karan Kumar\n"
            f"🏢 *Organization:* [CyberZoneAcademy](https://t.me/CyberZoneAcademy)"
        )
        try:
            bot = Bot(token=TELEGRAM_TOKEN)  # Initialize Bot with the token
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")
        except Exception as e:
            print(f"Error sending message: {e}")

async def send_startup_message_async():
    """Send a startup notification to Telegram."""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        message = (
            f"🌟 *Bitcoin Address Generator Script Started!* 🌟\n\n"
            f"🚀 *Welcome to the Bitcoin Address Generator Script!* 🚀\n\n"
            f"🔧 *Status:* Running\n"
            f"🔍 *Generating new addresses and checking balances.*\n\n"
            f"📈 *Developer:* Karan Kumar\n"
            f"🏢 *Organization:* [CyberZoneAcademy](https://t.me/CyberZoneAcademy)\n\n"
            f"✨ *Good luck, and may you find valuable addresses!* ✨"
        )
        try:
            bot = Bot(token=TELEGRAM_TOKEN)  # Initialize Bot with the token
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")
        except Exception as e:
            print(f"Error sending startup message: {e}")

async def notify_running_async():
    """Notify Telegram every hour that the script is running."""
    while True:
        await send_telegram_message_async("Script Running", "", "")
        await asyncio.sleep(3600)  # Sleep for one hour

def worker(counter, found_counter, lock, latest_details):
    """Generate keys from seed phrases, convert to addresses, and check against the rich list."""
    while True:
        seed_phrase = generate_seed_phrase()
        private_key, wif = seed_phrase_to_private_key(seed_phrase)
        public_key = private_key_to_public_key(private_key)
        address = public_key_to_address(public_key)
        with lock:
            counter.value += 1
            latest_details['address'] = address
            latest_details['seed_phrase'] = seed_phrase
            latest_details['balance'] = 0
            print(f"\r{Fore.GREEN}Addresses Generated: {counter.value}{Style.RESET_ALL}", end="")
        balance = check_balance(address)
        with lock:
            latest_details['balance'] = balance
        if balance > 0:
            with lock:
                found_counter.value += 1
            save_to_file(seed_phrase, address)
            asyncio.run(send_telegram_message_async(seed_phrase, address, balance))

def display_performance(counter, found_counter, lock, latest_details):
    """Display performance metrics periodically."""
    while True:
        with lock:
            key_count = counter.value
            found_count = found_counter.value
            latest_address = latest_details.get('address', 'N/A')
            latest_seed_phrase = latest_details.get('seed_phrase', 'N/A')
            latest_balance = latest_details.get('balance', '0 BTC')
        print(
            f"\r{Fore.CYAN}Addresses Generated: {key_count} - Matches Found: {found_count}{Style.RESET_ALL}\n"
            f"{Fore.YELLOW}Latest Address: {latest_address}{Style.RESET_ALL}\n"
            f"{Fore.YELLOW}Latest Seed Phrase: {latest_seed_phrase}{Style.RESET_ALL}\n"
            f"{Fore.YELLOW}Latest Balance: {latest_balance}{Style.RESET_ALL}",
            end=""
        )
        sleep(1)  # Update every second

def main():
    num_workers = multiprocessing.cpu_count()
    counter = Value("i", 0)
    found_counter = Value("i", 0)
    lock = Lock()
    latest_details = multiprocessing.Manager().dict()

    processes = [
        Process(target=worker, args=(counter, found_counter, lock, latest_details))
        for _ in range(num_workers)
    ]
    monitor = Process(target=display_performance, args=(counter, found_counter, lock, latest_details))
    notifier = Process(target=lambda: asyncio.run(notify_running_async()))

    # Send startup message
    asyncio.run(send_startup_message_async())

    for process in processes:
        process.start()
    monitor.start()
    notifier.start()

    try:
        monitor.join()  # Keep the main thread alive to allow monitoring and workers to run indefinitely
        notifier.join()  # Keep the notifier process alive
    except KeyboardInterrupt:
        for process in processes:
            process.terminate()
        monitor.terminate()
        notifier.terminate()
        for process in processes:
            process.join()
        monitor.join()
        notifier.join()

if __name__ == "__main__":
    main()
