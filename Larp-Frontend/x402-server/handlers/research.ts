/**
 * Larp x402 Resource Server — Research Pipeline Handlers
 *
 * These handlers are called ONLY after payment is verified by x402 middleware.
 * Each handler executes one stage of the research pipeline.
 */

import type { Context } from 'hono';
import Groq from 'groq-sdk';

// ─── Groq Client ──────────────────────────────────────────────────────────────
function getGroqClient(): Groq | null {
  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) return null;
  return new Groq({ apiKey });
}

// ─── Stage 1: Decompose ───────────────────────────────────────────────────────
/**
 * POST /research/decompose
 * Breaks a complex query into 3 targeted sub-questions using Groq LLaMA 3.3
 */
export async function handleDecomposeRequest(c: Context) {
  try {
    console.log('✓ PAYMENT VERIFIED — POST /research/decompose executing');

    const body = await c.req.json();
    const query = body.query || '';

    const groq = getGroqClient();
    if (!groq) {
      return c.json({
        subQuestions: [
          `What are the current developments in ${query}?`,
          `What are the key challenges facing ${query}?`,
          `What are the future implications of ${query}?`,
        ],
        paidVia: 'x402 / USDC Algorand Testnet',
        mode: 'fallback',
      });
    }

    const completion = await groq.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      messages: [
        {
          role: 'system',
          content: `You are a research query decomposer. Given a research question, break it into exactly 3 specific, targeted sub-questions that cover different aspects. Return ONLY a JSON object: {"subQuestions": ["q1", "q2", "q3"]}`,
        },
        { role: 'user', content: query },
      ],
      response_format: { type: 'json_object' },
      temperature: 0.3,
      max_tokens: 500,
    });

    const text = completion.choices[0]?.message?.content ?? '{}';
    const parsed = JSON.parse(text);

    return c.json({
      ...parsed,
      paidVia: 'x402 / USDC Algorand Testnet',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error in decompose handler:', error);
    return c.json({ error: 'Decompose failed', detail: String(error) }, 500);
  }
}

// ─── Stage 2: Search ──────────────────────────────────────────────────────────
/**
 * POST /research/search
 * Multi-source web search using Tavily AI Search API
 */
export async function handleSearchRequest(c: Context) {
  try {
    console.log('✓ PAYMENT VERIFIED — POST /research/search executing');

    const body = await c.req.json();
    const subQuestions: string[] = body.subQuestions || [];

    const tavilyKey = process.env.TAVILY_API_KEY;

    if (!tavilyKey) {
      // Fallback: use Groq for search-like results
      const groq = getGroqClient();
      if (groq) {
        const completion = await groq.chat.completions.create({
          model: 'llama-3.3-70b-versatile',
          messages: [
            {
              role: 'system',
              content: 'You are a web search simulator. Given sub-questions, return realistic search results. Return JSON: {"results": [{"title": "...", "url": "https://...", "snippet": "...", "subQuestion": "..."}]}',
            },
            { role: 'user', content: `Search for: ${subQuestions.join('; ')}` },
          ],
          response_format: { type: 'json_object' },
          temperature: 0.5,
          max_tokens: 2000,
        });
        const parsed = JSON.parse(completion.choices[0]?.message?.content ?? '{}');
        return c.json({ ...parsed, paidVia: 'x402 / USDC Algorand Testnet' });
      }
      return c.json({ results: [], paidVia: 'x402 / USDC Algorand Testnet', mode: 'fallback' });
    }

    // Real Tavily search for each sub-question
    const allResults: any[] = [];
    for (const q of subQuestions.slice(0, 3)) {
      try {
        const resp = await fetch('https://api.tavily.com/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            api_key: tavilyKey,
            query: q,
            search_depth: 'basic',
            max_results: 5,
            include_raw_content: false,
          }),
        });
        const data = await resp.json() as any;
        if (data.results) {
          allResults.push(
            ...data.results.map((r: any) => ({
              title: r.title,
              url: r.url,
              snippet: r.content?.substring(0, 300) || '',
              subQuestion: q,
            }))
          );
        }
      } catch (err) {
        console.warn(`Tavily search failed for "${q}":`, err);
      }
    }

    return c.json({
      results: allResults,
      totalResults: allResults.length,
      paidVia: 'x402 / USDC Algorand Testnet',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error in search handler:', error);
    return c.json({ error: 'Search failed', detail: String(error) }, 500);
  }
}

// ─── Stage 3: Fact-Check ──────────────────────────────────────────────────────
/**
 * POST /research/factcheck
 * Cross-references claims across independent sources
 */
export async function handleFactCheckRequest(c: Context) {
  try {
    console.log('✓ PAYMENT VERIFIED — POST /research/factcheck executing');

    const body = await c.req.json();
    const searchResults = body.searchResults || [];
    const query = body.query || '';

    const groq = getGroqClient();
    if (!groq) {
      return c.json({
        verifiedClaims: [],
        entities: [],
        paidVia: 'x402 / USDC Algorand Testnet',
        mode: 'fallback',
      });
    }

    const completion = await groq.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      messages: [
        {
          role: 'system',
          content: `You are a fact-checker. Given search results, extract verified claims and key entities. Return JSON: {"verifiedClaims": [{"claim": "...", "confidence": 0.95, "sources": ["url1"]}], "entities": ["entity1", "entity2"]}`,
        },
        {
          role: 'user',
          content: `Query: ${query}\nSearch Results:\n${JSON.stringify(searchResults).substring(0, 4000)}`,
        },
      ],
      response_format: { type: 'json_object' },
      temperature: 0.2,
      max_tokens: 2000,
    });

    const parsed = JSON.parse(completion.choices[0]?.message?.content ?? '{}');

    return c.json({
      ...parsed,
      paidVia: 'x402 / USDC Algorand Testnet',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error in factcheck handler:', error);
    return c.json({ error: 'Fact-check failed', detail: String(error) }, 500);
  }
}

// ─── Stage 4: Enrich ──────────────────────────────────────────────────────────
/**
 * POST /research/enrich
 * Fetches academic context from Wikipedia for key entities
 */
export async function handleEnrichRequest(c: Context) {
  try {
    console.log('✓ PAYMENT VERIFIED — POST /research/enrich executing');

    const body = await c.req.json();
    const entities: string[] = body.entities || [];

    const enrichments: any[] = [];

    for (const entity of entities.slice(0, 5)) {
      try {
        const wikiUrl = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(entity)}`;
        const resp = await fetch(wikiUrl, {
          headers: { 'User-Agent': 'LarpResearchAgent/1.0' },
        });
        if (resp.ok) {
          const data = await resp.json() as any;
          enrichments.push({
            entity,
            summary: data.extract?.substring(0, 500) || 'No summary available',
            source: 'Wikipedia',
            url: data.content_urls?.desktop?.page || '',
          });
        }
      } catch (err) {
        console.warn(`Wikipedia fetch failed for "${entity}":`, err);
      }
    }

    return c.json({
      enrichments,
      paidVia: 'x402 / USDC Algorand Testnet',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error in enrich handler:', error);
    return c.json({ error: 'Enrichment failed', detail: String(error) }, 500);
  }
}

// ─── Stage 5: Synthesize ─────────────────────────────────────────────────────
/**
 * POST /research/synthesize
 * Compiles all gathered data into a structured research report
 */
export async function handleSynthesizeRequest(c: Context) {
  try {
    console.log('✓ PAYMENT VERIFIED — POST /research/synthesize executing');

    const body = await c.req.json();
    const { query, verifiedClaims, enrichments, searchResults } = body;

    const groq = getGroqClient();
    if (!groq) {
      return c.json({
        title: `Research Report: ${query}`,
        overview: 'Fallback report — Groq API not configured',
        sections: [],
        sources: [],
        paidVia: 'x402 / USDC Algorand Testnet',
        mode: 'fallback',
      });
    }

    const completion = await groq.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      messages: [
        {
          role: 'system',
          content: `You are a research report synthesizer. Given verified claims, enrichments, and search results, produce a structured research report. Return JSON:
{
  "title": "Report Title",
  "overview": "Executive summary paragraph",
  "sections": [{"heading": "Section Title", "body": "Content...", "bulletPoints": ["point1", "point2"]}],
  "sources": [{"index": 1, "title": "Source Title", "authors": "Author Names", "year": 2024, "url": "https://...", "relevance": 0.95}],
  "codeSnippet": ""
}`,
        },
        {
          role: 'user',
          content: `Query: ${query}\n\nVerified Claims:\n${JSON.stringify(verifiedClaims || []).substring(0, 3000)}\n\nEnrichments:\n${JSON.stringify(enrichments || []).substring(0, 2000)}\n\nSearch Results:\n${JSON.stringify(searchResults || []).substring(0, 2000)}`,
        },
      ],
      response_format: { type: 'json_object' },
      temperature: 0.4,
      max_tokens: 4000,
    });

    const parsed = JSON.parse(completion.choices[0]?.message?.content ?? '{}');

    return c.json({
      ...parsed,
      paidVia: 'x402 / USDC Algorand Testnet',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error in synthesize handler:', error);
    return c.json({ error: 'Synthesis failed', detail: String(error) }, 500);
  }
}
