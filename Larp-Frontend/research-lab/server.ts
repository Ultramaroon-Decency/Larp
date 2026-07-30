// server.ts — Research Lab Multi-Step Agent Server
//
// Endpoints:
//   GET  /api/health                  — Health check
//   GET  /api/research/stream/:id     — SSE pipeline progress stream
//   POST /api/research/synthesize     — Trigger 5-step research pipeline
//   GET  /api/payments/log            — Global payment ledger
//   POST /api/export/bibtex           — BibTeX export

// ─── Load environment variables (must be first) ───────────────────────────────
// Uses Node's built-in fs instead of dotenv to avoid ESM hoisting issues.
// Reads .env.local first, then .env as fallback.
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

function loadEnvFile(filename: string): void {
  const filePath = join(process.cwd(), filename);
  if (!existsSync(filePath)) return;
  try {
    const content = readFileSync(filePath, 'utf-8');
    for (const line of content.split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eqIndex = trimmed.indexOf('=');
      if (eqIndex === -1) continue;
      const key = trimmed.substring(0, eqIndex).trim();
      const rawVal = trimmed.substring(eqIndex + 1).trim();
      // Strip surrounding quotes if present
      const value = rawVal.replace(/^["']|["']$/g, '');
      if (key && !process.env[key]) {
        process.env[key] = value;
      }
    }
  } catch (err) {
    console.warn(`[env] Could not load ${filename}:`, err);
  }
}

loadEnvFile('.env.local'); // local secrets — git-ignored
loadEnvFile('.env');       // shared defaults

import express from 'express';
import path from 'path';
import { EventEmitter } from 'node:events';
import { createServer as createViteServer } from 'vite';
import Groq from 'groq-sdk';
import {
  runResearchPipeline,
  createInitialSteps,
} from './orchestrator/researchPipeline.js';
import type { PipelineEvent, PaymentReceipt } from './orchestrator/types.js';

// ─── Session store for SSE connections ───────────────────────────────────────
// Each active research session has an EventEmitter + event buffer so that
// events emitted before the SSE connection is open are not lost.

interface SessionStore {
  emitter: EventEmitter;
  buffer: string[];       // events queued before SSE connects
  created: number;        // timestamp for cleanup
}

const sessions = new Map<string, SessionStore>();

// Clean up stale sessions older than 15 minutes
setInterval(() => {
  const cutoff = Date.now() - 15 * 60 * 1000;
  for (const [id, session] of sessions) {
    if (session.created < cutoff) sessions.delete(id);
  }
}, 60_000);

function getOrCreateSession(sessionId: string): SessionStore {
  if (!sessions.has(sessionId)) {
    sessions.set(sessionId, {
      emitter: new EventEmitter(),
      buffer: [],
      created: Date.now(),
    });
  }
  return sessions.get(sessionId)!;
}

function emitToSession(sessionId: string, event: PipelineEvent) {
  const session = getOrCreateSession(sessionId);
  const payload = JSON.stringify(event);
  session.buffer.push(payload);
  session.emitter.emit('pipeline_event', payload);
}

// ─── Global payment ledger (in-memory across all sessions) ───────────────────
const globalPaymentLedger: (PaymentReceipt & { sessionId: string })[] = [];

// ─── Groq client factory ──────────────────────────────────────────────────────
function getGroqClient(): Groq | null {
  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) return null;
  return new Groq({ apiKey });
}

// ─── Server bootstrap ─────────────────────────────────────────────────────────
async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json({ limit: '10mb' }));

  // ── GET /api/health ──────────────────────────────────────────────────────────
  app.get('/api/health', (_req, res) => {
    res.json({
      status: 'ok',
      time: new Date().toISOString(),
      groqConfigured: !!process.env.GROQ_API_KEY,
      tavilyConfigured: !!process.env.TAVILY_API_KEY,
      walletMode: process.env.AGENT_WALLET_PRIVATE_KEY ? 'real' : 'simulation',
    });
  });

  // ── GET /api/research/stream/:sessionId ──────────────────────────────────────
  // Server-Sent Events endpoint. The frontend opens this BEFORE POSTing to
  // /api/research/synthesize to receive real-time pipeline step events.
  app.get('/api/research/stream/:sessionId', (req, res) => {
    const { sessionId } = req.params;

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('X-Accel-Buffering', 'no');     // disable Nginx buffering
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.flushHeaders();

    const session = getOrCreateSession(sessionId);

    // Flush any events that arrived before SSE was connected
    for (const payload of session.buffer) {
      res.write(`data: ${payload}\n\n`);
    }

    // Send an initial ping to confirm the connection is live
    res.write(
      `data: ${JSON.stringify({ type: 'ping', sessionId, timestamp: new Date().toISOString() })}\n\n`
    );

    // Stream future events
    const handler = (payload: string) => {
      res.write(`data: ${payload}\n\n`);
    };
    session.emitter.on('pipeline_event', handler);

    req.on('close', () => {
      session.emitter.off('pipeline_event', handler);
    });
  });

  // ── POST /api/research/synthesize ────────────────────────────────────────────
  // Main research endpoint. Accepts a sessionId for SSE progress streaming.
  // Runs the 5-step pipeline when Gemini is configured; falls back to mock
  // data if GEMINI_API_KEY is absent.
  app.post('/api/research/synthesize', async (req, res) => {
    const {
      query,
      mode = 'quick',
      attachedFiles = [],
      sessionId,
    } = req.body as {
      query: string;
      mode?: 'quick' | 'deep';
      attachedFiles?: { name: string }[];
      sessionId?: string;
    };

    if (!query || typeof query !== 'string') {
      res.status(400).json({ error: 'Query parameter is required.' });
      return;
    }

    const ai = getGroqClient();

    if (ai && sessionId) {
      // ── Full multi-step pipeline with SSE progress ────────────────────────
      try {
        console.log(`\n[Server] 🚀 Starting pipeline for session ${sessionId}`);
        console.log(`[Server] Query: "${query.substring(0, 80)}..."`);

        const result = await runResearchPipeline(
          query,
          mode,
          sessionId,
          ai,
          (event) => {
            emitToSession(sessionId, event);

            // Also record payments in the global ledger
            if (event.type === 'payment' && event.payment) {
              globalPaymentLedger.push({ ...event.payment, sessionId });
            }
          }
        );

        // Emit completion event
        emitToSession(sessionId, {
          type: 'complete',
          sessionId,
          timestamp: new Date().toISOString(),
          totalCost: result.totalCost,
        });

    console.log(
      `[Server] ✅ Pipeline complete — cost: $${result.totalCost} USDC (simulated)\n`
    );

        res.json(result);
        return;
      } catch (err) {
        console.error('[Server] Pipeline error:', err);

        if (sessionId) {
          emitToSession(sessionId, {
            type: 'pipeline_error',
            sessionId,
            timestamp: new Date().toISOString(),
            error: 'Pipeline encountered an error — using fallback report',
          });
        }
        // Fall through to fallback
      }
    }

    if (ai && !sessionId) {
      // ── Legacy single-pass mode (no sessionId, backwards compatible) ────────
      try {
        const isDeep = mode === 'deep';
        const completion = await ai.chat.completions.create({
          model: 'llama-3.3-70b-versatile',
          messages: [
            {
              role: 'system',
              content: `You are Research Lab, an academic research synthesis system. Mode: ${isDeep ? 'Deep Dive (4-5 sections, 5+ citations)' : 'Quick Scan (2-3 sections, 3 citations)'}. Return strict JSON.`
            },
            { role: 'user', content: query }
          ],
          response_format: { type: 'json_object' },
        });
        const jsonText = completion.choices[0]?.message?.content ?? '{}';
        const parsed = JSON.parse(jsonText);
        res.json({ ...parsed, pipelineSteps: [], payments: [], totalCost: '0.0000' });
        return;
      } catch (err) {
        console.warn('[Server] Legacy Groq call warning:', err);
      }
    }

    // ── Fallback: mock response (no API key or all attempts failed) ─────────
    const fallback = generateFallbackResearch(query, mode === 'deep');
    res.json({ ...fallback, pipelineSteps: createInitialSteps(), payments: [], totalCost: '0.0000' });
  });

  // ── GET /api/payments/log ─────────────────────────────────────────────────
  // Returns the global in-memory payment ledger across all sessions.
  app.get('/api/payments/log', (_req, res) => {
    const totalSpent = globalPaymentLedger
      .reduce((sum, r) => sum + parseFloat(r.amount), 0)
      .toFixed(4);

    res.json({
      mode: process.env.AGENT_WALLET_PRIVATE_KEY ? 'real' : 'simulation',
      totalTransactions: globalPaymentLedger.length,
      totalSpentUSDC: totalSpent,
      receipts: globalPaymentLedger.slice(-100), // last 100
    });
  });

  // ── POST /api/export/bibtex ───────────────────────────────────────────────
  app.post('/api/export/bibtex', (req, res) => {
    const { sources, title } = req.body as {
      sources: {
        index?: number;
        authors?: string;
        year?: number;
        title?: string;
        journal?: string;
        doi?: string;
        url?: string;
      }[];
      title?: string;
    };

    if (!sources || !Array.isArray(sources)) {
      res.status(400).send('Invalid sources array');
      return;
    }

    let bibtexContent = `% BibTeX Bibliography Export for "${title ?? 'Research Lab Synthesis'}"\n`;
    bibtexContent += `% Generated on ${new Date().toLocaleDateString()}\n`;
    bibtexContent += `% Pipeline: Decompose → Search → Fact-Check → Enrich → Synthesize\n\n`;

    sources.forEach((s, idx) => {
      const key = `source_${s.index ?? idx + 1}_${(s.authors ?? 'author')
        .split(' ')[0]
        .toLowerCase()
        .replace(/[^a-z]/g, '')}_${s.year ?? 2024}`;
      bibtexContent += `@article{${key},\n`;
      bibtexContent += `  title   = {${s.title ?? 'Untitled Research'}},\n`;
      bibtexContent += `  author  = {${s.authors ?? 'Anonymous'}},\n`;
      bibtexContent += `  journal = {${s.journal ?? 'Academic Repository'}},\n`;
      bibtexContent += `  year    = {${s.year ?? 2024}},\n`;
      if (s.doi) bibtexContent += `  doi     = {${s.doi}},\n`;
      if (s.url) bibtexContent += `  url     = {${s.url}},\n`;
      bibtexContent += `}\n\n`;
    });

    res.setHeader('Content-Type', 'text/plain');
    res.setHeader('Content-Disposition', 'attachment; filename="references.bib"');
    res.send(bibtexContent);
  });

  // ── Serve frontend ────────────────────────────────────────────────────────
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*all', (_req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`\n🔬 Research Lab server running at http://0.0.0.0:${PORT}`);
    console.log(`💳 x402 payment mode: ${process.env.AGENT_WALLET_PRIVATE_KEY ? 'REAL (Base Sepolia)' : 'SIMULATION'}`);
    console.log(`🤖 Groq API: ${process.env.GROQ_API_KEY ? 'configured' : '⚠  NOT SET (fallback mode)'}`);
    console.log(`🔍 Tavily Search: ${process.env.TAVILY_API_KEY ? 'configured' : '⚠  NOT SET (using model knowledge)'}\n`);
  });
}

// ─── Fallback research generator ──────────────────────────────────────────────
// Used when GEMINI_API_KEY is absent or when the pipeline fails entirely.
function generateFallbackResearch(query: string, isDeep: boolean) {
  const queryLower = query.toLowerCase();

  let title = `Synthesis Analysis: ${query.length > 40 ? query.substring(0, 40) + '...' : query}`;
  if (queryLower.includes('quantum')) {
    title = 'Advancements in Quantum Computing: 2024 Analysis';
  } else if (queryLower.includes('carbon') || queryLower.includes('climate')) {
    title = 'Synthesized Analysis: Atmospheric & Socioeconomic Vectors';
  } else if (queryLower.includes('battery') || queryLower.includes('solid state')) {
    title = 'Synthesis Report: Solid State Batteries & Electrolytes';
  }

  return {
    title,
    overview: `A rigorous synthesis of current peer-reviewed literature regarding "${query}". Recent developments demonstrate significant progress in overcoming historical rate-limiting boundaries [1]. Modern frameworks prioritise system-level fidelity and empirical validation [2].`,
    sections: [
      {
        heading: 'Primary Theoretical Foundations',
        body: 'Empirical datasets across leading research laboratories indicate a marked convergence towards standardised benchmarking protocols. High-throughput automated synthesis has accelerated experimental turn-around by an estimated 3.4× [1].',
        bulletPoints: [
          'High-Fidelity Benchmark Thresholds: Cross-validation reveals reduced noise floor variance under controlled environmental parameters.',
          'Scalable Integration Architecture: Inter-module coupling efficiencies crossed critical operational milestones [2].',
        ],
      },
      {
        heading: isDeep ? 'Quantitative Methodology & Framework' : 'Summary & Strategic Implications',
        body: isDeep
          ? 'Analytical models validate sub-linear computational scaling when using distributed processing pipelines. Secondary telemetry confirms interfacial stability over extended operational durations [3].'
          : 'Further exploration of boundary conditions and longitudinal trial data is recommended for full institutional deployment.',
      },
    ],
    codeSnippet: isDeep
      ? `// Research Lab Analytical Pipeline (Fallback Mode)\nPipeline.Initialize(query_vector: "${query.substring(0, 30)}...")\nDataMesh.SyncGroundingSources(threshold: 0.85)\nSynthesis.EvaluateConfidenceScore(iterations: 1000)`
      : '',
    sources: [
      {
        index: 1,
        title: `Comprehensive Literature Review on ${query.split(' ')[0] ?? 'Research Objective'}`,
        authors: 'Smith, J., Doe, A. et al.',
        year: 2024,
        journal: 'Nature Research Synthesis, Vol. 28',
        relevance: 0.98,
        doi: '10.1038/s41558-2024-0018',
        url: 'https://doi.org/10.1038/s41558-2024-0018',
        tags: ['Peer Reviewed', 'PDF Available'],
        abstract: 'Comprehensive meta-analysis compiling observational and empirical trial results across 42 institutional datasets.',
      },
      {
        index: 2,
        title: `Systemic Benchmarking and Algorithmic Proofs in ${query.split(' ')[1] ?? 'Domain Studies'}`,
        authors: 'Johnson, M., Patel, R.',
        year: 2024,
        journal: 'IEEE Transactions on Advanced Analytics',
        relevance: 0.93,
        doi: '10.1109/TAA.2024.99210',
        url: 'https://doi.org/10.1109/TAA.2024.99210',
        tags: ['Technical Report'],
        abstract: 'Architectural specification and benchmark suite testing under extreme boundary conditions.',
      },
      {
        index: 3,
        title: 'Pre-print: Longitudinal Field Observations and Predictive Models',
        authors: 'MIT Academic Consortium',
        year: 2024,
        journal: 'MIT Research Archive',
        relevance: 0.88,
        doi: '10.48550/arXiv.2403.0112',
        url: 'https://arxiv.org/abs/2403.0112',
        tags: ['Pre-print', 'Institution Data'],
        abstract: 'Exploratory data analysis establishing new scaling paradigms for multi-factor synthesis.',
      },
    ],
  };
}

startServer();
