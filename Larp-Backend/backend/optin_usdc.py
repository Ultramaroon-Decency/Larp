"""
Opt-in both wallets to USDC ASA (10458941) on Algorand Testnet.

Run this ONCE after funding the wallets with ALGO.

Usage:
    cd Larp-Backend/backend
    python optin_usdc.py
"""

from algosdk import mnemonic, account
from algosdk.v2client import algod
from algosdk.transaction import AssetOptInTxn, wait_for_confirmation

USDC_ASA_ID = 10458941
ALGOD_URL = "https://testnet-api.algonode.cloud"

# Agent wallet mnemonic
AGENT_MNEMONIC = "sunny robust bomb yellow enter awkward damp amount motion combine frame acid close bus boost puzzle wonder glass melody wagon innocent tone thing absent divert"

def optin_to_usdc(wallet_mnemonic: str, wallet_name: str):
    """Opt-in a wallet to USDC ASA."""
    client = algod.AlgodClient("", ALGOD_URL)
    
    private_key = mnemonic.to_private_key(wallet_mnemonic)
    address = account.address_from_private_key(private_key)
    
    print(f"\n{'='*60}")
    print(f"Opting in {wallet_name}: {address}")
    print(f"ASA ID: {USDC_ASA_ID} (USDC on Testnet)")
    print(f"{'='*60}")
    
    # Check current account info
    info = client.account_info(address)
    algo_balance = info['amount'] / 1_000_000
    print(f"ALGO balance: {algo_balance}")
    
    # Check if already opted in
    for asset in info.get('assets', []):
        if asset['asset-id'] == USDC_ASA_ID:
            print(f"Already opted-in to USDC! Balance: {asset['amount'] / 1_000_000} USDC")
            return True
    
    if algo_balance < 0.2:
        print(f"Need at least 0.2 ALGO for opt-in. Current: {algo_balance}")
        return False
    
    # Create opt-in transaction
    params = client.suggested_params()
    txn = AssetOptInTxn(address, params, USDC_ASA_ID)
    signed_txn = txn.sign(private_key)
    
    tx_id = client.send_transaction(signed_txn)
    print(f"Opt-in TX submitted: {tx_id}")
    
    result = wait_for_confirmation(client, tx_id, 4)
    print(f"Opted-in successfully! Confirmed in round {result['confirmed-round']}")
    print(f"Lora: https://lora.algokit.io/testnet/transaction/{tx_id}")
    return True


if __name__ == "__main__":
    print("USDC ASA Opt-In Script for Algorand Testnet")
    print("=" * 60)
    
    # Opt-in agent wallet
    optin_to_usdc(AGENT_MNEMONIC, "Agent Wallet")
    
    print("\nDone! Now you can send/receive USDC on this wallet.")
