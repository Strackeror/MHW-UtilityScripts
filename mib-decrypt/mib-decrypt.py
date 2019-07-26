from Crypto.Cipher import Blowfish
import sys
import os


def endianness_reversal(data):
    return b''.join(map(lambda x: x[::-1],chunks(data, 4)))

def CapcomBlowfish(file):
    cipher = Blowfish.new("TZNgJfzyD2WKiuV4SglmI6oN5jP2hhRJcBwzUooyfIUTM4ptDYGjuRTP".encode("utf-8"), Blowfish.MODE_ECB)
    return endianness_reversal(cipher.decrypt(endianness_reversal(file)))

def CapcomBlowfishEncrypt(file):
    cipher = Blowfish.new("TZNgJfzyD2WKiuV4SglmI6oN5jP2hhRJcBwzUooyfIUTM4ptDYGjuRTP".encode("utf-8"), Blowfish.MODE_ECB)
    return endianness_reversal(cipher.encrypt(endianness_reversal(file)))

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

if (os.path.splitext(sys.argv[1]) == ".dec"):
    open(sys.argv[1][:-4], "wb").write(CapcomBlowfishEncrypt(open(sys.argv[1], 'rb').read()))
else:
    open(sys.argv[1] + ".dec", "wb").write(CapcomBlowfish(open(sys.argv[1], 'rb').read()))