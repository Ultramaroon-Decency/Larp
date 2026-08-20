import { x402ResourceServer, HTTPFacilitatorClient } from '@x402/core/server';
import { ALGORAND_TESTNET_CAIP2, ExactAvmScheme, USDC_TESTNET_ASA_ID } from '@x402/avm';
import type { Request, Response, NextFunction } from 'express';

const AVM_ADDRESS = process.env.AVM_ADDRESS || 'DECOMPOSEAPIGX402XASA10458941XALGORANDXTESTNETXADDR';
const FACILITATOR_URL = process.env.FACILITATOR_URL || 'https://facilitator.goplausible.xyz';

// Initialize the x402 Resource Server with GoPlausible Facilitator
const facilitatorClient = new HTTPFacilitatorClient({ url: FACILITATOR_URL });
export const x402Server = new x402ResourceServer(facilitatorClient)
  .register(ALGORAND_TESTNET_CAIP2, new ExactAvmScheme());

/**
 * Express Middleware to enforce x402 Payments on designated endpoints.
 */
export async function x402PaymentMiddleware(req: Request, res: Response, next: NextFunction) {
  // Only protect the main research synthesis endpoint (or add paths as needed)
  if (req.path !== '/api/research/synthesize') {
    return next();
  }

  // Preflight check
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE, HEAD');
    res.setHeader('Access-Control-Allow-Headers', '*');
    res.setHeader('Access-Control-Expose-Headers', '*');
    return res.sendStatus(200);
  }

  const sigHeader = req.header('payment-signature') || req.header('Payment-Signature');

  // Define payment requirements for /api/research/synthesize ($0.0035 USDC)
  const requirements = {
    scheme: 'exact' as const,
    price: '$0.0035',
    network: ALGORAND_TESTNET_CAIP2,
    payTo: AVM_ADDRESS,
    extra: { asset: Number(USDC_TESTNET_ASA_ID) },
  };

  // If no payment signature is present, return 402 Payment Required
  if (!sigHeader) {
    console.log(`[x402 Middleware] 402 challenge issued for ${req.path}`);
    res.setHeader('Payment-Required', 'true');
    res.setHeader('Payment-Response', JSON.stringify({ accepts: [requirements] }));
    res.setHeader('Access-Control-Expose-Headers', 'Payment-Required, Payment-Response');
    
    return res.status(402).json({
      statusCode: 402,
      message: 'Payment Required',
      accepts: [requirements]
    });
  }

  try {
    console.log(`[x402 Middleware] Payment-Signature found. Verifying via GoPlausible...`);
    
    // Decode base64 payment signature payload
    const payloadStr = Buffer.from(sigHeader, 'base64').toString('utf8');
    const paymentPayload = JSON.parse(payloadStr);

    // Verify on-chain payment with the facilitator
    const verifyResult = await x402Server.verifyPayment(paymentPayload, requirements);

    if (!verifyResult.success) {
      console.log(`[x402 Middleware] Verification failed: ${verifyResult.errorReason || 'Unknown error'}`);
      return res.status(400).json({
        error: 'Payment Verification Failed',
        reason: verifyResult.errorReason || 'Facilitator rejected payment transactions.'
      });
    }

    // Settle payment (mark transaction group as consumed to prevent replays)
    const settleResult = await x402Server.settlePayment(paymentPayload, requirements);
    if (!settleResult.success) {
      console.log(`[x402 Middleware] Settlement failed: ${settleResult.errorMessage || 'Unknown error'}`);
      return res.status(400).json({
        error: 'Payment Settlement Failed',
        reason: settleResult.errorMessage || 'Failed to settle transaction group.'
      });
    }

    console.log(`[x402 Middleware] ✅ Payment verified & settled: ${settleResult.transaction.id}`);
    next();
  } catch (err) {
    console.error('[x402 Middleware] Error processing payment verification:', err);
    return res.status(500).json({
      error: 'Internal Payment Processing Error',
      details: err instanceof Error ? err.message : String(err)
    });
  }
}
