// orchestrator/researchPipeline.ts
//
// Multi-Step Research Agent — 5-Stage Orchestration Pipeline
// ─────────────────────────────────────────────────────────────────────────────
//
// Pipeline stages:
//   1. DECOMPOSE  — Groq (Llama3) breaks query into 3 targeted sub-questions
//   2. SEARCH     — Tavily AI search API fetches real web results per sub-question
//                   (falls back to Groq knowledge if TAVILY_API_KEY not set)
//   3. FACT-CHECK — Groq cross-references results, extracts verified claims + entities
//   4. ENRICH     — Wikipedia REST API fetches academic context for key entities
//   5. SYNTHESIZE — Groq compiles all gathered data into a final cited research report
//
// Each step calls its API through the X402PaymentLayer (simulated payments),
// and emits SSE PipelineEvents so the frontend can show real-time progress.

import Groq from 'groq-sdk';
import { X402PaymentLayer } from './x402PaymentLayer.js';
import type {
  PipelineStep,
  PipelineEvent,
  ResearchPipelineResult,
  DecomposeResult,
  SearchResult,
  FactCheckResult,
  EnrichmentResult,
} from './types.js';

// ─── Pipeline step definitions ────────────────────────────────────────────────

// ─── Retry helper ─────────────────────────────────────────────────────────────
// Handles HTTP 429 (quota exceeded) by reading the retryDelay from the error
// body and waiting before retrying. Up to maxAttempts tries per API call.
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxAttempts = 3,
  stepName = 'API call'
): Promise<T> {
  let lastError: unknown;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (err: unknown) {
      lastError = err;

      const errStr = String(err);
      const is429 = errStr.includes('429') || errStr.includes('RESOURCE_EXHAUSTED') || errStr.includes('rate_limit');

      if (!is429 || attempt === maxAttempts) throw err;

      let waitMs = 15_000;
      const retryMatch = errStr.match(/retryDelay[":\s]+([0-9]+)s/);
      if (retryMatch) waitMs = Math.min(parseInt(retryMatch[1], 10) * 1000 + 2000, 65_000);

      console.warn(`[Pipeline] ${stepName}: rate limited (429), waiting ${waitMs / 1000}s before retry ${attempt}/${maxAttempts}...`);
      await new Promise((resolve) => setTimeout(resolve, waitMs));
    }
  }
  throw lastError;
}

export const PIPELINE_STEP_DEFINITIONS: Omit<PipelineStep, 'status'>[] = [
  {
    id: 'decompose',
    name: 'Query Decomposition',
    description: 'Breaking down your research question into targeted sub-queries',
    api: 'Groq / Llama3 (Decompose)',
  },
  {
    id: 'search',
    name: 'Multi-Source Search',
    description: 'Searching the web for each sub-query via Tavily AI Search',
    api: 'Tavily Search API',
  },
  {
    id: 'factcheck',
    name: 'Fact Verification',
    description: 'Cross-referencing findings and extracting verified claims',
    api: 'Groq / Llama3 (Fact-Check)',
  },
  {
    id: 'enrich',
    name: 'Knowledge Enrichment',
    description: 'Fetching supplementary context from Wikipedia knowledge base',
    api: 'Wikipedia API',
  },
  {
    id: 'synthesize',
    name: 'Report Synthesis',
    description: 'Compiling all data into a structured cited research report',
    api: 'Groq / Llama3 (Synthesize)',
  },
];

export function createInitialSteps(): PipelineStep[] {
  return PIPELINE_STEP_DEFINITIONS.map((s) => ({ ...s, status: 'pending' as const }));
}

// ─── Safe JSON parse ──────────────────────────────────────────────────────────

function safeParseJSON<T>(text: string | undefined | null, fallback: T): T {
  if (!text) return fallback;
  // Extract JSON from markdown code block if present
  const jsonMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/) || text.match(/(\{[\s\S]*\})/);
  const raw = jsonMatch ? jsonMatch[1] : text;
  try {
    return JSON.parse(raw.trim()) as T;
  } catch {
    return fallback;
  }
}

// ─── Groq chat completion helper ──────────────────────────────────────────────

async function groqChat(
  groq: Groq,
  systemPrompt: string,
  userPrompt: string,
  jsonMode = false
): Promise<string> {
  const completion = await groq.chat.completions.create({
    model: 'llama-3.3-70b-versatile',
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt },
    ],
    temperature: 0.3,
    max_tokens: 4096,
    ...(jsonMode ? { response_format: { type: 'json_object' } } : {}),
  });
  return completion.choices[0]?.message?.content ?? '';
}

// ─── Tavily search helper ─────────────────────────────────────────────────────

interface TavilyResult {
  title: string;
  url: string;
  content: string;
  score: number;
}

async function tavilySearch(query: string, apiKey: string): Promise<string> {
  const response = await fetch('https://api.tavily.com/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      query,
      search_depth: 'advanced',
      max_results: 5,
      include_answer: true,
      include_raw_content: false,
    }),
  });

  if (!response.ok) {
    throw new Error(`Tavily search failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json() as {
    answer?: string;
    results?: TavilyResult[];
  };

  const parts: string[] = [];
  if (data.answer) parts.push(`Summary: ${data.answer}`);
  if (data.results) {
    for (const r of data.results) {
      parts.push(`\n[${r.title}]\nURL: ${r.url}\n${r.content}`);
    }
  }

  return parts.join('\n\n');
}

// ─── Pipeline runner ──────────────────────────────────────────────────────────

export async function runResearchPipeline(
  query: string,
  mode: 'quick' | 'deep',
  sessionId: string,
  groq: Groq,
  emit: (event: PipelineEvent) => void
): Promise<ResearchPipelineResult> {
  const payment = new X402PaymentLayer();
  const steps = createInitialSteps();
  const pipelineStart = Date.now();
  const tavilyKey = process.env.TAVILY_API_KEY ?? '';

  const updateStep = (id: string, patch: Partial<PipelineStep>) => {
    const step = steps.find((s) => s.id === id)!;
    Object.assign(step, patch);
    return step;
  };

  const emitStart = (id: string) => {
    const step = updateStep(id, { status: 'running' });
    emit({ type: 'step_start', sessionId, timestamp: new Date().toISOString(), step: { ...step } });
  };

  const emitDone = (id: string, cost?: string) => {
    const step = updateStep(id, {
      status: 'done',
      cost,
      duration: Date.now() - pipelineStart,
    });
    emit({ type: 'step_done', sessionId, timestamp: new Date().toISOString(), step: { ...step } });
  };

  const emitError = (id: string, error: string) => {
    const step = updateStep(id, { status: 'error', error });
    emit({ type: 'step_error', sessionId, timestamp: new Date().toISOString(), step: { ...step }, error });
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // STEP 1: DECOMPOSE
  // ═══════════════════════════════════════════════════════════════════════════
  emitStart('decompose');

  let decomposed: DecomposeResult = {
    subQuestions: [query],
    researchDomain: 'General Research',
    mainThesis: query,
  };

  try {
    const { result, receipt } = await payment.callWithPayment(
      'decompose',
      'Query Decomposition',
      'Groq / Llama3 (Decompose)',
      () => retryWithBackoff(async () => {
        const text = await groqChat(
          groq,
          'You are an expert research strategist. You MUST respond with ONLY valid JSON — no markdown, no explanation.',
          `Decompose this research query into exactly 3 specific, searchable sub-questions:

Query: "${query}"

Respond with ONLY this JSON (no markdown):
{
  "subQuestions": ["sub-question 1", "sub-question 2", "sub-question 3"],
  "researchDomain": "e.g. Climate Science",
  "mainThesis": "One sentence summarising the core research objective"
}`,
          true
        );
        return safeParseJSON<DecomposeResult>(text, decomposed);
      }, 3, 'Decompose')
    );

    emit({ type: 'payment', sessionId, timestamp: new Date().toISOString(), payment: receipt });
    decomposed = result;
    emitDone('decompose', `${receipt.amount} USDC`);
    console.log(`[Pipeline] Decomposed into ${decomposed.subQuestions.length} sub-questions`);
  } catch (err) {
    console.warn('[Pipeline] Step 1 (Decompose) failed:', err);
    emitError('decompose', 'Decomposition failed — using original query');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // STEP 2: SEARCH (Tavily AI search, falls back to Groq knowledge)
  // ═══════════════════════════════════════════════════════════════════════════
  emitStart('search');

  const searchResults: SearchResult[] = [];

  try {
    const questionsToSearch = mode === 'quick'
      ? decomposed.subQuestions.slice(0, 2)
      : decomposed.subQuestions;

    for (const subQuestion of questionsToSearch) {
      const apiName = tavilyKey ? 'Tavily Search API' : 'Groq / Llama3 (Search)';

      const { result, receipt } = await payment.callWithPayment(
        'search',
        `Search: ${subQuestion.substring(0, 40)}...`,
        apiName,
        () => retryWithBackoff(async () => {
          if (tavilyKey) {
            // Real web search via Tavily
            return await tavilySearch(subQuestion, tavilyKey);
          } else {
            // Fallback: use Groq's training knowledge
            return await groqChat(
              groq,
              'You are a research assistant with broad knowledge of academic literature and current events. Provide detailed, factual information.',
              `Research question: "${subQuestion}"\n\nProvide a comprehensive summary of what is known about this topic. Include key facts, statistics, findings, and reference any relevant studies, researchers, or organisations you know of.`,
              false
            );
          }
        }, 3, `Search`)
      );

      emit({ type: 'payment', sessionId, timestamp: new Date().toISOString(), payment: receipt });
      searchResults.push({ query: subQuestion, text: result });
    }

    emitDone('search', `${payment.totalCost} USDC total`);
    console.log(`[Pipeline] Searched ${searchResults.length} sub-questions`);
  } catch (err) {
    console.warn('[Pipeline] Step 2 (Search) failed:', err);
    emitError('search', 'Search failed — proceeding with limited data');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // STEP 3: FACT-CHECK
  // ═══════════════════════════════════════════════════════════════════════════
  emitStart('factcheck');

  let factCheck: FactCheckResult = {
    verifiedClaims: [],
    keyEntities: [],
    confidence: 0.75,
  };

  try {
    const combinedSearchText = searchResults
      .map((r) => `[${r.query}]\n${r.text}`)
      .join('\n\n---\n\n')
      .substring(0, 8000);

    const { result, receipt } = await payment.callWithPayment(
      'factcheck',
      'Fact Verification',
      'Groq / Llama3 (Fact-Check)',
      () => retryWithBackoff(async () => {
        const text = await groqChat(
          groq,
          'You are a rigorous academic fact-checker. You MUST respond with ONLY valid JSON — no markdown, no explanation.',
          `Review these search results about "${query}":

${combinedSearchText}

Extract the most well-supported claims and key entities. Respond with ONLY this JSON:
{
  "verifiedClaims": ["specific claim 1", "specific claim 2", "specific claim 3", "specific claim 4"],
  "keyEntities": ["entity1", "entity2", "entity3"],
  "confidence": 0.85
}`,
          true
        );
        return safeParseJSON<FactCheckResult>(text, factCheck);
      }, 3, 'Fact-Check')
    );

    emit({ type: 'payment', sessionId, timestamp: new Date().toISOString(), payment: receipt });
    factCheck = result;
    emitDone('factcheck', `${receipt.amount} USDC`);
    console.log(`[Pipeline] Fact-checked: ${factCheck.verifiedClaims.length} claims`);
  } catch (err) {
    console.warn('[Pipeline] Step 3 (Fact-Check) failed:', err);
    emitError('factcheck', 'Fact-check failed — proceeding with unverified data');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // STEP 4: ENRICH (Wikipedia REST API)
  // ═══════════════════════════════════════════════════════════════════════════
  emitStart('enrich');

  const enrichments: EnrichmentResult[] = [];

  try {
    const entitiesToEnrich = factCheck.keyEntities.length > 0
      ? factCheck.keyEntities.slice(0, 2)
      : [decomposed.researchDomain];

    for (const entity of entitiesToEnrich) {
      const { result, receipt } = await payment.callWithPayment(
        'enrich',
        `Enrich: ${entity}`,
        'Wikipedia API',
        async (): Promise<EnrichmentResult> => {
          const encodedEntity = encodeURIComponent(entity.trim());
          const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodedEntity}`;

          const response = await fetch(url, {
            headers: {
              'User-Agent': 'ResearchLabAgent/1.0',
              'Accept': 'application/json',
            },
          });

          if (!response.ok) return { entity, summary: '', url: '' };

          const data = await response.json() as {
            extract?: string;
            content_urls?: { desktop?: { page?: string } };
          };

          return {
            entity,
            summary: data.extract ?? '',
            url: data.content_urls?.desktop?.page ?? `https://en.wikipedia.org/wiki/${encodedEntity}`,
          };
        }
      );

      emit({ type: 'payment', sessionId, timestamp: new Date().toISOString(), payment: receipt });
      if (result.summary) enrichments.push(result);
    }

    emitDone('enrich', `${payment.totalCost} USDC total`);
    console.log(`[Pipeline] Enriched ${enrichments.length} entities via Wikipedia`);
  } catch (err) {
    console.warn('[Pipeline] Step 4 (Enrich) failed:', err);
    emitError('enrich', 'Enrichment failed — proceeding without Wikipedia data');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // STEP 5: SYNTHESIZE
  // ═══════════════════════════════════════════════════════════════════════════
  emitStart('synthesize');

  try {
    const isDeep = mode === 'deep';

    const contextBlock = [
      `RESEARCH QUERY: "${query}"`,
      `DOMAIN: ${decomposed.researchDomain}`,
      `MODE: ${isDeep ? 'Deep Dive (4-5 sections, 5+ sources)' : 'Quick Scan (2-3 sections, 3-4 sources)'}`,
      '',
      '── SUB-QUESTIONS RESEARCHED ──',
      ...decomposed.subQuestions.map((q, i) => `${i + 1}. ${q}`),
      '',
      '── SEARCH FINDINGS ──',
      ...searchResults.map((r) => `[${r.query}]\n${r.text.substring(0, 2000)}`),
      '',
      '── VERIFIED CLAIMS ──',
      ...factCheck.verifiedClaims.map((c, i) => `[${i + 1}] ${c}`),
      '',
      '── KEY ENTITIES ──',
      factCheck.keyEntities.join(', '),
      '',
      '── WIKIPEDIA ENRICHMENT ──',
      ...(enrichments.length > 0
        ? enrichments.map((e) => `${e.entity}:\n${e.summary.substring(0, 400)}`)
        : ['No enrichment data available.']),
    ].join('\n');

    const systemPrompt = `You are Research Lab, a world-class academic research synthesis engine.
Synthesise the provided research intelligence into a comprehensive, authoritative, cited report.

RULES:
- Inline citations must match sources array: [1], [2], [3]
- Every factual claim must have a citation
- Sources should be real, verifiable papers or publications
- Use verified claims and Wikipedia data for academic context
${isDeep
  ? '- Deep Dive: 4-5 detailed sections, include code/formula snippet if relevant, 5+ sources'
  : '- Quick Scan: 2-3 concise sections, 3-4 sources'}

You MUST respond with ONLY valid JSON — no markdown wrapper, no explanation before or after. Pure JSON only.

Schema:
{
  "title": "string",
  "overview": "string with [1] style citations",
  "sections": [{ "heading": "string", "body": "string", "bulletPoints": ["string"] }],
  "codeSnippet": "string or empty string",
  "sources": [{
    "index": 1,
    "title": "string",
    "authors": "string",
    "year": 2024,
    "journal": "string",
    "relevance": 0.95,
    "doi": "string",
    "url": "string",
    "tags": ["string"],
    "abstract": "string"
  }]
}`;

    const { result: finalReport, receipt } = await payment.callWithPayment(
      'synthesize',
      'Report Synthesis',
      'Groq / Llama3 (Synthesize)',
      () => retryWithBackoff(async () => {
        const text = await groqChat(groq, systemPrompt, contextBlock, true);
        return safeParseJSON(text, {
          title: `Research Report: ${query.substring(0, 50)}`,
          overview: 'Synthesis could not be completed.',
          sections: [],
          codeSnippet: '',
          sources: [],
        });
      }, 3, 'Synthesize')
    );

    emit({ type: 'payment', sessionId, timestamp: new Date().toISOString(), payment: receipt });
    emitDone('synthesize', `${receipt.amount} USDC`);
    console.log(`[Pipeline] ✅ Complete — total cost: $${payment.totalCost} USDC (simulated)`);

    return {
      ...(finalReport as {
        title: string;
        overview: string;
        sections: { heading: string; body: string; bulletPoints?: string[] }[];
        codeSnippet: string;
        sources: {
          index: number; title: string; authors: string; year: number;
          journal: string; relevance: number; doi: string; url: string;
          tags: string[]; abstract: string;
        }[];
      }),
      pipelineSteps: steps,
      payments: payment.ledger,
      totalCost: payment.totalCost,
    };
  } catch (err) {
    console.error('[Pipeline] Step 5 (Synthesize) failed:', err);
    emitError('synthesize', String(err));
    throw new Error(`Pipeline synthesis failed: ${err}`);
  }
}
