/**
 * Larp x402 Resource Server
 *
 * Payment-protected research API endpoints on Algorand TestNet.
 * Uses the official x402 SDK with GoPlausible facilitator for
 * real on-chain payment verification.
 *
 * Architecture:
 *   - Hono web framework with @x402/hono payment middleware
 *   - HTTPFacilitatorClient → GoPlausible for verification
 *   - ExactAvmScheme for Algorand TestNet (CAIP-2)
 *   - 5 research endpoints, each requiring USDC micropayment
 *
 * Start: npm start (runs on port 4021)
 * Test:  curl http://localhost:4021/health
 */

import { config } from 'dotenv';
import { Hono } from 'hono';
import { serve } from '@hono/node-server';
import { paymentMiddleware } from '@x402/hono';
import { x402ResourceServer, HTTPFacilitatorClient } from '@x402/core/server';
import type { ResourceServerExtension } from '@x402/core/types';
import { ExactAvmScheme } from '@x402/avm/exact/server';
import { bazaarResourceServerExtension } from '@x402-avm/extensions';

// The SDK's ALGORAND_TESTNET_CAIP2 truncates the genesis hash, but the
// GoPlausible facilitator requires the FULL base64 CAIP-2 identifier.
// This is the exact value from https://facilitator.goplausible.xyz/supported
const ALGORAND_TESTNET_CAIP2 = 'algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=';

// Import research pipeline handlers
import {
  handleDecomposeRequest,
  handleSearchRequest,
  handleFactCheckRequest,
  handleEnrichRequest,
  handleSynthesizeRequest,
} from './handlers/research.js';

// Import endpoint configuration
import createPaymentConfig, { EndpointConfig } from './endpoints.config.js';

// Load environment variables
config();

// ════════════════════════════════════════════════════════════════════
// CONFIGURATION & SETUP
// ════════════════════════════════════════════════════════════════════

const avmAddress = process.env.AVM_ADDRESS;
const facilitatorUrl = process.env.FACILITATOR_URL;
const port = parseInt(process.env.PORT || '4021', 10);

// Validate required environment
if (!avmAddress || !facilitatorUrl) {
  console.error(
    '❌ Missing required environment variables:\n' +
    '   - AVM_ADDRESS (your Algorand wallet receiving payments)\n' +
    '   - FACILITATOR_URL (x402 facilitator service)'
  );
  process.exit(1);
}

console.log('\n' + '═'.repeat(60));
console.log('LARP x402 RESEARCH RESOURCE SERVER');
console.log('═'.repeat(60));
console.log('Configuration:');
console.log(`  Receiver Address: ${avmAddress}`);
console.log(`  Facilitator: ${facilitatorUrl}`);
console.log(`  Port: ${port}`);
console.log(`  Groq API: ${process.env.GROQ_API_KEY ? '✓ configured' : '⚠ not set'}`);
console.log(`  Tavily API: ${process.env.TAVILY_API_KEY ? '✓ configured' : '⚠ not set'}`);
console.log('═'.repeat(60) + '\n');

// Initialize x402 Resource Server with GoPlausible facilitator
const facilitatorClient = new HTTPFacilitatorClient({ url: facilitatorUrl });
const x402Server = new x402ResourceServer(facilitatorClient)
  .register(ALGORAND_TESTNET_CAIP2, new ExactAvmScheme())
  .registerExtension(bazaarResourceServerExtension as unknown as ResourceServerExtension);

// Create Hono app
const app = new Hono();

// ════════════════════════════════════════════════════════════════════
// MIDDLEWARE STACK
// ════════════════════════════════════════════════════════════════════

/**
 * CORS Middleware — Required for x402 payment headers
 */
app.use('*', async (c, next) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, PUT, DELETE, HEAD',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Expose-Headers': '*',
    'Access-Control-Max-Age': '86400',
  };

  if (c.req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  Object.entries(corsHeaders).forEach(([key, value]) => {
    c.header(key, value);
  });

  await next();
});

/**
 * Logging Middleware
 */
app.use('*', async (c, next) => {
  const timestamp = new Date().toISOString();
  console.log(`\n[${timestamp}] ${c.req.method.toUpperCase()} ${c.req.path}`);

  if (c.req.header('payment-signature')) {
    console.log('  ✓ Payment-Signature header detected');
  }

  await next();
  console.log(`  Response: ${c.res.status}`);
});

/**
 * x402 Payment Middleware
 * Applies payment protection to all configured endpoints
 */
const paymentConfig: EndpointConfig = createPaymentConfig(avmAddress);
console.log('📋 Payment-Protected Research Endpoints:');
Object.entries(paymentConfig).forEach(([route, config]) => {
  const price = config.accepts[0]?.price || 'unknown';
  console.log(`   ${route} — ${price} USDC — ${config.description}`);
});
console.log();

app.use(paymentMiddleware(paymentConfig as any, x402Server));

// ════════════════════════════════════════════════════════════════════
// PAYMENT-PROTECTED RESEARCH ENDPOINTS
// ════════════════════════════════════════════════════════════════════

// Stage 1: Query Decomposition — $0.001 USDC
app.post('/research/decompose', handleDecomposeRequest);

// Stage 2: Multi-Source Search — $0.0025 USDC
app.post('/research/search', handleSearchRequest);

// Stage 3: Fact Verification — $0.0015 USDC
app.post('/research/factcheck', handleFactCheckRequest);

// Stage 4: Knowledge Enrichment — $0.0005 USDC
app.post('/research/enrich', handleEnrichRequest);

// Stage 5: Report Synthesis — $0.0035 USDC
app.post('/research/synthesize', handleSynthesizeRequest);

// ════════════════════════════════════════════════════════════════════
// PUBLIC ENDPOINTS — No payment required
// ════════════════════════════════════════════════════════════════════

/**
 * Health check — verify server is running
 */
app.get('/health', (c) => {
  return c.json({
    status: 'ok',
    service: 'larp-x402-research-server',
    network: 'Algorand TestNet',
    uptime: process.uptime(),
    groqConfigured: !!process.env.GROQ_API_KEY,
    tavilyConfigured: !!process.env.TAVILY_API_KEY,
  });
});

/**
 * Info — shows all configured endpoints and pricing
 */
app.get('/info', (c) => {
  return c.json({
    service: 'larp-x402-research-server',
    version: '1.0.0',
    network: 'Algorand TestNet',
    receiver: avmAddress,
    facilitator: facilitatorUrl,
    endpoints: Object.entries(paymentConfig).map(([route, cfg]) => ({
      route,
      price: cfg.accepts[0]?.price,
      description: cfg.description,
    })),
  });
});

// ════════════════════════════════════════════════════════════════════
// ERROR HANDLING
// ════════════════════════════════════════════════════════════════════

app.notFound((c) => {
  return c.json(
    {
      error: 'Endpoint not found',
      path: c.req.path,
      hint: 'Try GET /health or GET /info for diagnostics',
    },
    404
  );
});

// ════════════════════════════════════════════════════════════════════
// SERVER STARTUP
// ════════════════════════════════════════════════════════════════════

serve({ fetch: app.fetch, port }, () => {
  console.log('\n✅ Larp x402 Research Server is running!\n');
  console.log('═'.repeat(60));
  console.log('Endpoints:');
  console.log(`  API:     http://localhost:${port}`);
  console.log(`  Health:  http://localhost:${port}/health`);
  console.log(`  Info:    http://localhost:${port}/info`);
  console.log('═'.repeat(60));
  console.log('\n📚 Test commands:\n');
  console.log(`  curl http://localhost:${port}/health`);
  console.log(`  curl http://localhost:${port}/info`);
  console.log(`  curl -X POST http://localhost:${port}/research/decompose`);
  console.log('  (↑ will return 402 Payment Required)\n');
  console.log('═'.repeat(60) + '\n');
});
