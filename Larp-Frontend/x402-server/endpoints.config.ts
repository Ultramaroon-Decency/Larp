/**
 * Larp x402 Resource Server — Endpoint Configuration
 *
 * Defines payment-protected research pipeline endpoints.
 * Each endpoint maps to a research pipeline step and requires
 * a USDC micropayment on Algorand Testnet.
 */

import { USDC_TESTNET_ASA_ID } from '@x402/avm';
import { declareDiscoveryExtension } from '@x402-avm/extensions';

// The SDK's ALGORAND_TESTNET_CAIP2 truncates the genesis hash, but the
// GoPlausible facilitator requires the FULL base64 CAIP-2 identifier.
// This is the exact value from https://facilitator.goplausible.xyz/supported
const ALGORAND_TESTNET_CAIP2 = 'algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=';

export interface EndpointConfig {
  [key: string]: {
    accepts: Array<{
      scheme: 'exact';
      price: string;
      network: string;
      payTo: string;
      extra: { asset: number };
    }>;
    description: string;
    extensions?: Record<string, unknown>;
  };
}

/**
 * Payment configuration for all research pipeline endpoints.
 * Total cost per full research query: ~$0.0085 USDC
 */
export function createPaymentConfig(avmAddress: string): EndpointConfig {
  return {
    // ══════════════════════════════════════════════════════════════════
    // RESEARCH PIPELINE ENDPOINTS — Payment-Protected
    // ══════════════════════════════════════════════════════════════════

    /**
     * Stage 1: Query Decomposition
     * Breaks a complex research query into 3 targeted sub-questions
     * using Groq LLaMA 3.3 70B
     */
    'POST /research/decompose': {
      accepts: [
        {
          scheme: 'exact',
          price: '$0.001',
          network: ALGORAND_TESTNET_CAIP2,
          payTo: avmAddress,
          extra: { asset: Number(USDC_TESTNET_ASA_ID) },
        },
      ],
      description: 'Query decomposition — Break query into sub-questions — $0.001 USDC',
      extensions: declareDiscoveryExtension({
        bodyType: 'json',
        input: { query: 'quantum computing advances 2024' },
        output: {
          example: {
            subQuestions: [
              'What are the latest quantum computing breakthroughs?',
              'How do quantum algorithms compare to classical algorithms?',
              'What are commercial applications of quantum computing?',
            ],
            paidVia: 'x402 / USDC Algorand Testnet',
          },
        },
      }),
    },

    /**
     * Stage 2: Multi-Source Web Search
     * Searches for evidence across multiple sources using Tavily AI
     */
    'POST /research/search': {
      accepts: [
        {
          scheme: 'exact',
          price: '$0.0025',
          network: ALGORAND_TESTNET_CAIP2,
          payTo: avmAddress,
          extra: { asset: Number(USDC_TESTNET_ASA_ID) },
        },
      ],
      description: 'Web search — Multi-source evidence gathering — $0.0025 USDC',
      extensions: declareDiscoveryExtension({
        bodyType: 'json',
        input: { subQuestions: ['query1', 'query2'] },
        output: {
          example: {
            results: [{ title: 'Research Paper', url: 'https://...', snippet: '...' }],
            paidVia: 'x402 / USDC Algorand Testnet',
          },
        },
      }),
    },

    /**
     * Stage 3: Fact Verification
     * Cross-references claims across independent search results
     */
    'POST /research/factcheck': {
      accepts: [
        {
          scheme: 'exact',
          price: '$0.0015',
          network: ALGORAND_TESTNET_CAIP2,
          payTo: avmAddress,
          extra: { asset: Number(USDC_TESTNET_ASA_ID) },
        },
      ],
      description: 'Fact verification — Cross-reference claims — $0.0015 USDC',
      extensions: declareDiscoveryExtension({
        bodyType: 'json',
        input: { claims: ['claim1', 'claim2'], sources: [] },
        output: {
          example: {
            verifiedClaims: [{ claim: '...', confidence: 0.95, sources: ['...'] }],
            paidVia: 'x402 / USDC Algorand Testnet',
          },
        },
      }),
    },

    /**
     * Stage 4: Knowledge Enrichment
     * Fetches academic context from Wikipedia for key entities
     */
    'POST /research/enrich': {
      accepts: [
        {
          scheme: 'exact',
          price: '$0.0005',
          network: ALGORAND_TESTNET_CAIP2,
          payTo: avmAddress,
          extra: { asset: Number(USDC_TESTNET_ASA_ID) },
        },
      ],
      description: 'Knowledge enrichment — Academic context — $0.0005 USDC',
      extensions: declareDiscoveryExtension({
        bodyType: 'json',
        input: { entities: ['quantum computing', 'qubits'] },
        output: {
          example: {
            enrichments: [{ entity: 'Quantum Computing', summary: '...', source: 'Wikipedia' }],
            paidVia: 'x402 / USDC Algorand Testnet',
          },
        },
      }),
    },

    /**
     * Stage 5: Report Synthesis
     * Compiles all verified data into a structured research report
     */
    'POST /research/synthesize': {
      accepts: [
        {
          scheme: 'exact',
          price: '$0.0035',
          network: ALGORAND_TESTNET_CAIP2,
          payTo: avmAddress,
          extra: { asset: Number(USDC_TESTNET_ASA_ID) },
        },
      ],
      description: 'Report synthesis — Final research compilation — $0.0035 USDC',
      extensions: declareDiscoveryExtension({
        bodyType: 'json',
        input: { query: '...', verifiedClaims: [], enrichments: [] },
        output: {
          example: {
            title: 'Research Report',
            sections: [],
            sources: [],
            totalCost: '0.0085 USDC',
            paidVia: 'x402 / USDC Algorand Testnet',
          },
        },
      }),
    },
  };
}

export default createPaymentConfig;
