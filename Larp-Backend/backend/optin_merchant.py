"""
Opt-in MERCHANT wallet to USDC ASA (10458941) on Algorand Testnet.
The agent wallet is already opted-in.

Usage:
    python optin_merchant.py
"""

from algosdk import mnemonic, account
from algosdk.v2client import algod
from algosdk.transaction import AssetOptInTxn, PaymentTxn, wait_for_confirmation

USDC_ASA_ID = 10458941
ALGOD_URL = "https://testnet-api.algonode.cloud"

# Merchant wallet mnemonic (receives USDC payments)
MERCHANT_MNEMONIC = "cancel tide average suspect tube chair garlic enemy hobby help hedgehog lounge educate quit welcome shadow slush fitness craft camp candy cupboard panel ability gesture"

# Agent wallet mnemonic (has ALGO to fund merchant)
AGENT_MNEMONIC = "sunny robust bomb yellow enter awkward damp amount motion combine frame acid close bus boost puzzle wonder glass melody wagon innocent tone thing absent divert"


def check_and_optin(wallet_mnemonic, wallet_name):
    """Check wallet status and opt-in to USDC if needed."""
    client = algod.AlgodClient("", ALGOD_URL)

    private_key = mnemonic.to_private_key(wallet_mnemonic)
    address = account.address_from_private_key(private_key)

    print(f"{'='*60}")
    print(f"{wallet_name}: {address}")
    print(f"{'='*60}")

    info = client.account_info(address)
    algo_balance = info["amount"] / 1_000_000
    print(f"  ALGO balance: {algo_balance}")

    # Check if already opted in
    for asset in info.get("assets", []):
        if asset["asset-id"] == USDC_ASA_ID:
            usdc_bal = asset["amount"] / 1_000_000
            print(f"  USDC balance: {usdc_bal}")
            print(f"  Already opted-in to USDC!")
            return address, algo_balance

    print(f"  NOT opted-in to USDC yet")
    return address, algo_balance


def fund_with_algo(from_mnemonic, to_address, amount_algo=0.3):
    """Send ALGO from one wallet to another."""
    client = algod.AlgodClient("", ALGOD_URL)
    private_key = mnemonic.to_private_key(from_mnemonic)
    sender = account.address_from_private_key(private_key)

    params = client.suggested_params()
    amount_microalgo = int(amount_algo * 1_000_000)

    txn = PaymentTxn(sender, params, to_address, amount_microalgo)
    signed_txn = txn.sign(private_key)

    tx_id = client.send_transaction(signed_txn)
    print(f"  Funding TX submitted: {tx_id}")

    wait_for_confirmation(client, tx_id, 4)
    print(f"  Sent {amount_algo} ALGO to merchant wallet")
    return True


def optin_to_usdc(wallet_mnemonic, wallet_name):
    """Opt-in a wallet to USDC ASA."""
    client = algod.AlgodClient("", ALGOD_URL)

    private_key = mnemonic.to_private_key(wallet_mnemonic)
    address = account.address_from_private_key(private_key)

    # Check if already opted in
    info = client.account_info(address)
    for asset in info.get("assets", []):
        if asset["asset-id"] == USDC_ASA_ID:
            print(f"  {wallet_name} already opted-in!")
            return True

    params = client.suggested_params()
    txn = AssetOptInTxn(address, params, USDC_ASA_ID)
    signed_txn = txn.sign(private_key)

    tx_id = client.send_transaction(signed_txn)
    print(f"  Opt-in TX submitted: {tx_id}")

    result = wait_for_confirmation(client, tx_id, 4)
    print(f"  Opted-in! Confirmed in round {result['confirmed-round']}")
    print(f"  Lora: https://lora.algokit.io/testnet/transaction/{tx_id}")
    return True


if __name__ == "__main__":
    print("USDC Opt-In for Merchant Wallet")
    print()

    # Check merchant wallet status
    merchant_addr, merchant_algo = check_and_optin(MERCHANT_MNEMONIC, "Merchant Wallet")

    # If merchant has less than 0.2 ALGO, fund it from agent
    if merchant_algo < 0.2:
        print(f"\n  Merchant needs ALGO for opt-in. Sending 0.3 ALGO from agent...")
        fund_with_algo(AGENT_MNEMONIC, merchant_addr, 0.3)

    # Opt-in merchant to USDC
    print(f"\n  Opting merchant into USDC (ASA {USDC_ASA_ID})...")
    optin_to_usdc(MERCHANT_MNEMONIC, "Merchant")

    print("\n" + "="*60)
    print("DONE! Merchant wallet can now receive USDC payments.")
    print("Restart the backend and try a research query.")
    print("="*60)
