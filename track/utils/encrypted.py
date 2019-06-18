import struct
import socket

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding


class EncryptedSocket:
    def __init__(self):
        self.socket = None
        self.encrypt = None
        self.decrypt = None
        self.padder = padding.PKCS7(128).padder()
        self.unpadder = padding.PKCS7(128).unpadder()

    def open(self, address, port):
        """
            open a socket to address, port and initialize the encryption layer by exchanging a key
            using X25519. The key is used as an AES key throughout the communication.
            If the connection fails a new AES key will be issued.

            :param address:
            :param port:
            :return: self
        """
        self.socket = socket.create_connection((address, port))

        private_key = X25519PrivateKey.generate()
        pubkey = private_key.public_key().public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )

        # send client public key
        self.socket.send(pubkey)

        # receive server public Key
        data = self.socket.recv(32)

        # from public key get shared_key
        server_key = X25519PublicKey.from_public_bytes(data)
        shared_key = private_key.exchange(server_key)

        key = HKDF(
            algorithm=hashes.SHA256(),
            length=48,
            salt=None,
            info=b'handshake data',
            backend=default_backend()
        ).derive(shared_key)

        cipher = Cipher(algorithms.AES(key[0:32]), modes.CBC(key[32:]), backend=default_backend())
        self.encrypt = cipher.encryptor()
        self.decrypt = cipher.decryptor()
        return self

    def listen(self, address, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((address, port))
        self.socket.listen()
        return self

    def accept(self):
        """
            accept an incoming connection & initialize the encryption layer for that client
            :return: self
        """

        clt, addr = self.socket.accept()

        # Generate a private key
        server_key = X25519PrivateKey.generate()

        pubkey = server_key.public_key().public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )

        data = clt.recv(32)   # Receive client public Key
        clt.sendall(pubkey)    # send public key to client

        public_key = X25519PublicKey.from_public_bytes(data)

        # get Shared key
        shared_key = server_key.exchange(public_key)
        shared_key = HKDF(
            algorithm=hashes.SHA256(),
            length=48,
            salt=None,
            info=b'handshake data',
            backend=default_backend()
        ).derive(shared_key)

        encrypted_socket = EncryptedSocket()
        encrypted_socket.socket = clt

        cipher = Cipher(algorithms.AES(shared_key[0:32]), modes.CBC(shared_key[32:]), backend=default_backend())

        encrypted_socket.encrypt = cipher.encryptor()
        encrypted_socket.decrypt = cipher.decryptor()

        return encrypted_socket, addr

    def sendall(self, bytes):
        padded_bytes = self.padder.update(bytes)
        padded_bytes += self.padder.finalize()

        encrypted = self.encrypt.update(padded_bytes)
        encrypted += self.encrypt.finalize()

        size = bytearray(struct.pack('I', len(encrypted) + 4))
        self.socket.sendall(size + encrypted)

    def recvall(self):
        data = self.socket.recv(4096)
        size = struct.unpack('I', data[0:4])[0]

        # receive everything
        while len(data) != size:
            data += self.socket.recv(4096)

        if size == len(data):
            data = data[4:]

            decrypted = self.decrypt.update(data)
            decrypted += self.decrypt.finalize()

            unpadded = self.unpadder.update(decrypted)
            unpadded += self.unpadder.finalize()

            return unpadded
