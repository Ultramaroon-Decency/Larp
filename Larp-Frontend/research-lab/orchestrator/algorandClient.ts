import algosdk from 'algosdk';

/**
 * Algorand Testnet Client Configurator
 */

export function getAlgodClient(): algosdk.Algodv2 {
  const server = process.env.ALGOD_SERVER || 'https://testnet-api.algonode.cloud';
  const port = process.env.ALGOD_PORT || '';
  const token = process.env.ALGOD_TOKEN || '';
  return new algosdk.Algodv2(token, server, port);
}

export function getIndexerClient(): algosdk.Indexer {
  const server = process.env.INDEXER_SERVER || 'https://testnet-idx.algonode.cloud';
  const port = process.env.INDEXER_PORT || '';
  const token = process.env.INDEXER_TOKEN || '';
  return new algosdk.Indexer(token, server, port);
}

/**
 * Recovers an Algorand Account from a 25-word mnemonic passphrase.
 */
export function getAccountFromMnemonic(mnemonic: string): algosdk.Account {
  const trimmed = mnemonic.trim();
  if (!trimmed) {
    throw new Error('Mnemonic passphrase is empty');
  }
  return algosdk.mnemonicToSecretKey(trimmed);
}

/**
 * Generates a transaction link to the Lora Algorand Explorer.
 */
export function getExplorerUrl(txId: string): string {
  return `https://lora.algokit.io/testnet/transaction/${txId}`;
}

/**
 * Returns the Testnet USDC Asset ID.
 */
export function getUSDCAssetId(): number {
  const assetId = process.env.USDC_TESTNET_ASA_ID || '10458941';
  return parseInt(assetId, 10);
}
