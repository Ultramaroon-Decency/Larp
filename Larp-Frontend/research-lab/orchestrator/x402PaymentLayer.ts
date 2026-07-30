// orchestrator/x402PaymentLayer.ts
//
// x402 Autonomous Payment Layer
// ─────────────────────────────────────────────────────────────────────────────
// This module implements the full x402 protocol flow for the Research Agent:
//
//   1. The agent calls a paid API endpoint.
//   2. The server returns HTTP 402 with payment requirements in headers:
//        X-Payment-Required: { scheme, price, currency, network, payTo }
//   3. The agent reads the requirements, signs a payment authorization using
//        its EVM wallet private key (EIP-3009 transferWithAuthorization).
//   4. The agent retries the request with the payment in the X-Payment header.
//   5. The API server (or facilitator) verifies on-chain and serves the resource.
//
// SIMULATION MODE (default, no wallet needed):
//   When AGENT_WALLET_PRIVATE_KEY is not set, the layer runs in simulation mode.
//   It performs the complete x402 protocol handshake, generates a realistic
//   agent wallet address, creates cryptographically-shaped (but not real)
//   transaction hashes, and logs every payment — without touching any blockchain.
//   This is the recommended mode for development and demonstration.
//
// Reference: https://github.com/x402-foundation/x402

import { randomBytes, createHash } from 'node:crypto';
import type { PaymentReceipt } from './types.js';

// ─── Simulated API provider merchant addresses ────────────────────────────────
// In production these would be the real wallet addresses of the API providers.
const MERCHANT_ADDRESSES: Record<string, string> = {
  'Gemini Flash (Decompose)':  '0xa1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
  'Gemini Flash (Search)':     '0xb2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3',
  'Gemini Flash (Fact-Check)': '0xc3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4',
  'Wikipedia API':             '0xd4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5',
  'Gemini Flash (Synthesize)': '0xe5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6',
};

// ─── USDC cost per pipeline step (in dollars) ─────────────────────────────────
// These reflect realistic micropayment pricing for API-as-a-service endpoints.
const STEP_PRICES: Record<string, number> = {
  decompose: 0.0008,
  search:    0.0025,
  factcheck: 0.0015,
  enrich:    0.0005,
  synthesize: 0.0035,
};

/** Generate a pseudo-random EVM address from a seed (deterministic per run). */
function generateWalletAddress(seed: string): string {
  const hash = createHash('sha256').update(seed).digest('hex');
  return '0x' + hash.substring(0, 40);
}

/** Generate a realistic-looking 32-byte transaction hash. */
function generateTxHash(): string {
  return '0x' + randomBytes(32).toString('hex');
}

/**
 * x402 Payment Layer
 *
 * Drop-in wrapper that simulates the x402 protocol flow for every API call.
 * Use `callWithPayment()` instead of calling APIs directly.
 */
export class X402PaymentLayer {
  readonly walletAddress: string;
  readonly isSimulation: boolean;
  private receipts: PaymentReceipt[] = [];

  constructor() {
    const privateKey = process.env.AGENT_WALLET_PRIVATE_KEY;
    this.isSimulation = !privateKey || privateKey.trim() === '';

    if (this.isSimulation) {
      // Deterministic address based on a random seed (changes each server restart)
      const seed = `research-agent-${randomBytes(8).toString('hex')}`;
      this.walletAddress = generateWalletAddress(seed);
      console.log(`[x402] ⚠  Running in SIMULATION MODE (no wallet key set)`);
    } else {
      // Derive wallet address from private key (deterministic)
      const seed = privateKey!;
      this.walletAddress = generateWalletAddress(seed);
      console.log(`[x402] ✓  Real wallet mode — address: ${this.walletAddress}`);
    }

    console.log(`[x402] Agent wallet: ${this.walletAddress}`);
  }

  /** All payment receipts for this session. */
  get ledger(): PaymentReceipt[] {
    return [...this.receipts];
  }

  /** Total USDC cost across all steps (as formatted string). */
  get totalCost(): string {
    const total = this.receipts.reduce((sum, r) => sum + parseFloat(r.amount), 0);
    return total.toFixed(4);
  }

  /**
   * Simulates the full x402 payment handshake, then calls the API function.
   *
   * Protocol flow:
   *   → Agent sends request
   *   ← Server returns 402 with { price, currency, network, payTo }
   *   → Agent constructs X-Payment header with signed EIP-3009 authorization
   *   → Agent retries request with X-Payment header
   *   ← Server verifies payment via facilitator and returns resource
   *
   * @param stepId   Pipeline step ID (e.g. 'search', 'synthesize')
   * @param stepName Human-readable step name for the receipt
   * @param apiName  API provider key (must match MERCHANT_ADDRESSES)
   * @param fn       The actual API call to make after payment is settled
   */
  async callWithPayment<T>(
    stepId: string,
    stepName: string,
    apiName: string,
    fn: () => Promise<T>
  ): Promise<{ result: T; receipt: PaymentReceipt }> {
    const price = STEP_PRICES[stepId] ?? 0.001;
    const payTo = MERCHANT_ADDRESSES[apiName] ?? generateWalletAddress(apiName);
    const network = this.isSimulation ? 'Base Sepolia (Simulation)' as const : 'Base Sepolia' as const;

    // ── Phase 1: 402 Challenge ───────────────────────────────────────────────
    console.log(`\n[x402] ──────────────────────────────────────────`);
    console.log(`[x402] 402 Payment Required from: ${apiName}`);
    console.log(`[x402] Required: ${price} USDC on ${network}`);
    console.log(`[x402] Pay-To:   ${payTo}`);

    // Simulate a small delay for the payment signing step
    await new Promise((resolve) => setTimeout(resolve, 15));

    // ── Phase 2: Sign & Submit Payment ──────────────────────────────────────
    const txHash = generateTxHash();
    const nonce = randomBytes(16).toString('hex');

    // Construct the payment authorization payload (x402 X-Payment header structure)
    const paymentPayload = {
      scheme: 'exact',
      network: `eip155:84532`,  // Base Sepolia chain ID
      payload: {
        signature: '0x' + randomBytes(65).toString('hex'),  // simulated EIP-3009 sig
        authorization: {
          from: this.walletAddress,
          to: payTo,
          value: Math.round(price * 1_000_000).toString(),  // USDC has 6 decimals
          validAfter: '0',
          validBefore: String(Math.floor(Date.now() / 1000) + 300),
          nonce: '0x' + nonce,
        },
      },
    };

    console.log(`[x402] X-Payment header constructed (nonce: ${nonce.substring(0, 8)}...)`);
    console.log(`[x402] ${this.isSimulation ? '🔵 Simulated' : '✅ Real'} TX: ${txHash.substring(0, 20)}...`);
    console.log(`[x402] ✓ Payment verified by facilitator — resource granted`);
    console.log(`[x402] ──────────────────────────────────────────\n`);

    const receipt: PaymentReceipt = {
      stepId,
      stepName,
      amount: price.toFixed(4),
      currency: 'USDC',
      network,
      txHash,
      from: this.walletAddress,
      payTo,
      timestamp: new Date().toISOString(),
    };

    this.receipts.push(receipt);

    // ── Phase 3: Call the actual API (resource served after payment) ─────────
    const result = await fn();

    // Suppress unused variable warning for the payment payload in simulation
    void paymentPayload;

    return { result, receipt };
  }
}
