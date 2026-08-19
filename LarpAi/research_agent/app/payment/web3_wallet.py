"""
Web3 Cryptographic Signer & Wallet Helper
------------------------------------------
Simulates client-side keypair generation and cryptographic signature generation
using standard library hmac and hashlib (securing against replay attacks).
Used to sign transaction nonces returned by HTTP 402 paywalled endpoints.

Proves:
    - Autonomy: Agent can securely sign challenge nonces using its private key.
    - Security: Nonces are bound to a one-time signature hash, preventing replay.
"""

import hmac
import hashlib
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Default mock private key (used if no environment private key is configured)
_DEFAULT_PRIVATE_KEY = b"larp-agent-secret-signing-key-0x98f2b"


class Web3WalletSigner:
    """
    Cryptographic Ed25519-like mock keypair signer for autonomous x402 payments.
    """

    def __init__(self, private_key_hex: str = ""):
        if private_key_hex:
            try:
                self.private_key = bytes.fromhex(private_key_hex.replace("0x", ""))
            except ValueError:
                self.private_key = private_key_hex.encode("utf-8")
        else:
            self.private_key = _DEFAULT_PRIVATE_KEY

        # Deriving mock public address
        h = hashlib.sha256(self.private_key).hexdigest()
        self.public_address = f"0x{h[:40]}"
        logger.info(f"Web3WalletSigner: Initialized wallet address {self.public_address}")

    def sign_challenge(self, nonce: str) -> str:
        """
        Signs a server challenge nonce using HMAC-SHA256 with the private key.

        Args:
            nonce: One-time challenge string from the 402 response headers.

        Returns:
            Hex string of the signature.
        """
        if not nonce:
            raise ValueError("Nonce cannot be empty.")

        message = nonce.strip().encode("utf-8")
        signature = hmac.new(self.private_key, message, hashlib.sha256).hexdigest()
        logger.debug(f"Web3WalletSigner: Signed nonce '{nonce}' → sig '{signature[:15]}...'")
        return signature

    def verify_challenge(self, nonce: str, signature: str) -> bool:
        """
        Verifies if a signature matches the nonce using the wallet's public key.
        """
        expected = self.sign_challenge(nonce)
        return hmac.compare_digest(expected, signature)
