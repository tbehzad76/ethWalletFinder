import requests
from eth_keys import keys
import os
import time
import sqlite3

def create_db():
    # اتصال به پایگاه داده (در صورت عدم وجود، آن را ایجاد می‌کند)
    conn = sqlite3.connect('checked_wallets.db')

    # ایجاد جدول برای ذخیره آدرس‌ها
    conn.execute('''
    CREATE TABLE IF NOT EXISTS wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT UNIQUE
    )
    ''')
    # تایید تغییرات و بستن ارتباط
    conn.commit()
    conn.close()

def get_eth_balance(address, api_key):
    url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1':
            balance_in_wei = int(data['result'])
            balance_in_eth = balance_in_wei / 10**18
            return balance_in_eth
    return None

def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, json=payload)
    return response

def is_wallet_checked(address):
    conn = sqlite3.connect('checked_wallets.db')
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM wallets WHERE address=?", (address,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_wallet_address(address):
    conn = sqlite3.connect('checked_wallets.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO wallets (address) VALUES (?)", (address,))
    conn.commit()
    conn.close()

# جایگزین کنید با کلید API خود از اترسکن
api_key = ''
# جایگزین کنید با توکن ربات تلگرام
bot_token = ('')
# جایگزین کنید با Chat ID شما
chat_id = ''

create_db()
# اجرای بی‌نهایت
while True:
    private_key_bytes = os.urandom(32)
    private_key = keys.PrivateKey(private_key_bytes)
    public_key = private_key.public_key
    address = public_key.to_checksum_address()

    # بررسی اینکه آیا این آدرس قبلاً بررسی شده است
    if not is_wallet_checked(address):
        # دریافت موجودی آدرس
        balance = get_eth_balance(address, api_key)

        # ذخیره آدرس در دیتابیس
        save_wallet_address(address)

        if balance is not None and balance > 0:
            message = (f"Found non-zero balance!\n"
                       f"Address: {address}\n"
                       f"Balance: {balance} ETH\n"
                       f"Private Key: {private_key}")
            response = send_telegram_message(bot_token, chat_id, message)
            if response.status_code == 200:
                print("Message sent successfully")
            else:
                print("Failed to send message")
            break

    # تنظیم تاخیر برای محدود کردن درخواست‌ها به 100,000 در روز
    time.sleep(0.864)