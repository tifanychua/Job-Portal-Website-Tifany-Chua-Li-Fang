from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()


SECRET_KEY = os.getenv("MESSAGE_ENCRYPTION_KEY")


if SECRET_KEY is None:
    raise Exception("MESSAGE_ENCRYPTION_KEY is not configured")


cipher = Fernet(SECRET_KEY.encode())


def encrypt_message(message: str):

    return cipher.encrypt(message.encode()).decode()


def decrypt_message(encrypted_message: str):

    return cipher.decrypt(encrypted_message.encode()).decode()
