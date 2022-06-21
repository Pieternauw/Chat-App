from cryptography.fernet import Fernet 
import os 
import sys

path = os.getcwd()
path += "\\build.c"



if sys.argv[1] == "decrypt":
    with open('filekey.key', 'rb') as filekey:
        key = filekey.read()

    fernet = Fernet(key)

    with open(path, 'rb') as enc_file:
        encrypted = enc_file.read()

    decrypted = fernet.decrypt(encrypted)

    with open(path, 'wb') as dec_file:
        dec_file.write(decrypted)
elif sys.argv[1] == "encrypt":
    #key
    key = Fernet.generate_key()

    with open('filekey.key', 'wb') as filekey:
        filekey.write(key)

    with open('filekey.key', 'rb') as filekey:
            key = filekey.read()

    fernet = Fernet(key)

    with open(path, 'rb') as file:
        original = file.read()

    encrypted = fernet.encrypt(original)

    with open(path, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)
else:
    print("no arguments given")