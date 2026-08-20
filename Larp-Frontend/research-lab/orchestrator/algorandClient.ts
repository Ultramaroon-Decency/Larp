// orchestrator/algorandClient.ts
//
// Algorand Testnet Client Helper
// ─────────────────────────────────────────────────────────────────────────────
// Provides a unified interface for:
//   1. Algod client   — transaction building & submission (testnet-api.algonode.cloud)
//   2. Indexer client — transaction lookup & verification (testnet-idx.algonode.cloud)
//   3. Account loader — derives keypair from ALGORAND_AGENT_MNEMONIC (algosdk)
//   4. USDC ASA config — Testnet USDC Asset ID 10458941
//   5. Lora Explorer  — builds clickable receipt URLs (lora.algokit.io)
//
// Reference: https://developer.algorand.org/docs/sdks/javascript/

import algosdk from 'algosdk';

// ─── Network Configuration ───────────────────────────────────────────────────

/** CAIP-2 identifier for Algorand Testnet (genesis hash-based). */
export const ALGORAND_TESTNET_CAIP2 =
  'algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=';

/** USDC Testnet ASA (Algorand Standard Asset) ID. */
export const USDC_TESTNET_ASA_ID = 10458941;

/** Default Algod server (AlgoNode public Testnet endpoint). */
const DEFAULT_ALGOD_SERVER =
  process.env.ALGOD_SERVER || 'https://testnet-api.algonode.cloud';
const DEFAULT_ALGOD_PORT = process.env.ALGOD_PORT || '';
const DEFAULT_ALGOD_TOKEN = process.env.ALGOD_TOKEN || '';

/** Default Indexer server (AlgoNode public Testnet endpoint). */
const DEFAULT_INDEXER_SERVER =
  process.env.INDEXER_SERVER || 'https://testnet-idx.algonode.cloud';
const DEFAULT_INDEXER_PORT = process.env.INDEXER_PORT || '';
const DEFAULT_INDEXER_TOKEN = process.env.INDEXER_TOKEN || '';

// ─── Client Factories ────────────────────────────────────────────────────────

/** Create an Algod client for Algorand Testnet. */
export function getAlgodClient(): algosdk.Algodv2 {
  return new algosdk.Algodv2(
    DEFAULT_ALGOD_TOKEN,
    DEFAULT_ALGOD_SERVER,
    DEFAULT_ALGOD_PORT,
  );
}

/** Create an Indexer client for Algorand Testnet. */
export function getIndexerClient(): algosdk.Indexer {
  return new algosdk.Indexer(
    DEFAULT_INDEXER_TOKEN,
    DEFAULT_INDEXER_SERVER,
    DEFAULT_INDEXER_PORT,
  );
}

// ─── Account Management ──────────────────────────────────────────────────────

export interface AlgorandAccount {
  addr: string;
  sk: Uint8Array;
}

/**
 * Load an Algorand account from a 25-word mnemonic.
 *
 * @param mnemonic  25-word Algorand mnemonic phrase
 * @returns         Account object with `addr` (public address) and `sk` (secret key)
 * @throws          Error if mnemonic is invalid or missing
 */
export function loadAccountFromMnemonic(mnemonic: string): AlgorandAccount {
  if (!mnemonic || mnemonic.trim().split(/\s+/).length < 25) {
    throw new Error(
      'Invalid Algorand mnemonic. Expected 25 space-separated words.',
    );
  }
  const account = algosdk.mnemonicToSecretKey(mnemonic.trim());
  return { addr: account.addr, sk: account.sk };
}

/**
 * Try to load the agent account from environment.
 * Returns null if ALGORAND_AGENT_MNEMONIC is not set (simulation mode).
 */
export function tryLoadAgentAccount(): AlgorandAccount | null {
  const mnemonic = process.env.ALGORAND_AGENT_MNEMONIC;
  if (!mnemonic || mnemonic.trim() === '') {
    return null;
  }
  try {
    return loadAccountFromMnemonic(mnemonic);
  } catch (err) {
    console.warn(
      `[AlgorandClient] Failed to load agent account from mnemonic: ${err}`,
    );
    return null;
  }
}

// ─── Receiver Address ────────────────────────────────────────────────────────

/** Get the configured AVM receiver (merchant) address. */
export function getReceiverAddress(): string {
  return process.env.AVM_ADDRESS || '';
}

// ─── Transaction Explorer ────────────────────────────────────────────────────

/**
 * Build a clickable Lora Algorand Explorer URL for a given Transaction ID.
 *
 * @param txId  The Algorand Transaction ID (52-char base32)
 * @returns     Full URL to the Lora Explorer transaction page
 *
 * @example
 *   getLoraExplorerUrl('A1B2C3...')
 *   // => 'https://lora.algokit.io/testnet/transaction/A1B2C3...'
 */
export function getLoraExplorerUrl(txId: string): string {
  const network = process.env.ALGORAND_NETWORK || 'testnet';
  return `https://lora.algokit.io/${network}/transaction/${txId}`;
}

// ─── Facilitator URL ─────────────────────────────────────────────────────────

/** Get the GoPlausible facilitator URL for x402 payment verification. */
export function getFacilitatorUrl(): string {
  return (
    process.env.FACILITATOR_URL || 'https://facilitator.goplausible.xyz'
  );
}
