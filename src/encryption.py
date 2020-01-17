#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from cryptography.fernet import Fernet
text = input("Text: ")
key_text = input("Encryption Key: ")
if key_text:
    key = key_text
else:
    key = Fernet.generate_key()

print(f"KEY = {key}")

cipher_suite = Fernet(key)

encoded_text = cipher_suite.encrypt(text.encode())
print(f"encoded_text = \'{encoded_text.decode('utf-8')}\'")
decoded_text = cipher_suite.decrypt(encoded_text)
print(f"decoded_text = \'{decoded_text.decode('utf-8')}\'")
