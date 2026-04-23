// ============================================================
// ROSTR — Agent Runtime (Multi-LLM Router + Chat)
// ============================================================

import { compilePAL, type TaskSpec } from './pal.js';
import { hybridSearch } from '../core/search.js';
import { getBrainEngine } from '../core/engine.js';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  message: string;
  taskSpec?: TaskSpec;
  sources?: Array<{ slug: string; title: string }>;
  model: string;
}

// LLM Provider interface
interface LLMProvider {
  name: string;
  chat(messages: ChatMessage[], opts?: { stream?: boolean }): Promise<string>;
  available(): boolean;
}

class OpenAIProvider implements LLMProvider {
  name = 'openai';
  private model: string;
  available() { const k = process.env.OPENAI_API_KEY; return !!(k && k !== 'sk-...'); }

  constructor() { this.model = process.env.AGENT_MODEL || 'gpt-4o-mini'; }

  async chat(messages: ChatMessage[]): Promise<string> {
    const res = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${process.env.OPENAI_API_KEY}` },
      body: JSON.stringify({ model: this.model, messages, temperature: 0.7, max_tokens: 4096 }),
    });
    if (!res.ok) throw new Error(`OpenAI: ${res.statusText}`);
    const data = await res.json() as { choices: Array<{ message: { content: string } }> };
    return data.choices[0]?.message?.content || '';
  }
}

class AnthropicProvider implements LLMProvider {
  name = 'anthropic';
  available() { const k = process.env.ANTHROPIC_API_KEY; return !!(k && k !== 'sk-ant-...'); }

  async chat(messages: ChatMessage[]): Promise<string> {
    const system = messages.find(m => m.role === 'system')?.content || '';
    const userMsgs = messages.filter(m => m.role !== 'system').map(m => ({ role: m.role, content: m.content }));

    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ANTHROPIC_API_KEY!,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({ model: 'claude-sonnet-4-20250514', max_tokens: 4096, system, messages: userMsgs }),
    });
    if (!res.ok) throw new Error(`Anthropic: ${res.statusText}`);
    const data = await res.json() as { content: Array<{ text: string }> };
    return data.content[0]?.text || '';
  }
}

class DeepSeekProvider implements LLMProvider {
  name = 'deepseek';
  available() { return !!process.env.DEEPSEEK_API_KEY; }

  async chat(messages: ChatMessage[]): Promise<string> {
    const res = await fetch('https://api.deepseek.com/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${process.env.DEEPSEEK_API_KEY}` },
      body: JSON.stringify({ model: 'deepseek-chat', messages, temperature: 0.7 }),
    });
    if (!res.ok) throw new Error(`DeepSeek: ${res.statusText}`);
    const data = await res.json() as { choices: Array<{ message: { content: string } }> };
    return data.choices[0]?.message?.content || '';
  }
}

class GroqProvider implements LLMProvider {
  name = 'groq';
  available() { const k = process.env.GROQ_API_KEY; return !!(k && k !== 'gsk_...'); }

  async chat(messages: ChatMessage[]): Promise<string> {
    const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${process.env.GROQ_API_KEY}` },
      body: JSON.stringify({ model: 'llama-3.1-70b-versatile', messages, temperature: 0.7 }),
    });
    if (!res.ok) throw new Error(`Groq: ${res.statusText}`);
    const data = await res.json() as { choices: Array<{ message: { content: string } }> };
    return data.choices[0]?.message?.content || '';
  }
}

// Provider chain: OpenAI → Anthropic → DeepSeek → Groq
const providers: LLMProvider[] = [
  new OpenAIProvider(),
  new AnthropicProvider(),
  new DeepSeekProvider(),
  new GroqProvider(),
];

export function getAvailableProvider(): LLMProvider | null {
  return providers.find(p => p.available()) || null;
}

export function listProviders(): Array<{ name: string; available: boolean }> {
  return providers.map(p => ({ name: p.name, available: p.available() }));
}

const SYSTEM_PROMPT = `You are ROSTR, an AI agent powered by the ROSTR Agent Framework.
You have access to a persistent knowledge brain, session memory (ContextEngine), and an NPAO task system.

Your capabilities:
- Search and retrieve from the knowledge brain
- Remember context across sessions
- Classify and manage tasks using NPAO (Necessity → Anxiety → Priority → Opportunity)
- Compile prompts through PAL (Prompt Abstraction Layer)

Be concise, accurate, and cite your sources when referencing brain knowledge.
If you don't know something, say so — never hallucinate.`;

export async function chat(userMessage: string, history: ChatMessage[] = []): Promise<ChatResponse> {
  const provider = getAvailableProvider();
  if (!provider) {
    return {
      message: '⚠️ No LLM provider configured. Add an API key to .env (OPENAI_API_KEY, ANTHROPIC_API_KEY, DEEPSEEK_API_KEY, or GROQ_API_KEY).',
      model: 'none',
    };
  }

  // Run PAL compilation
  let taskSpec: TaskSpec | undefined;
  try {
    taskSpec = await compilePAL(userMessage);
  } catch { /* PAL is best-effort */ }

  // Brain-first: search for relevant context
  let brainContext = '';
  const sources: Array<{ slug: string; title: string }> = [];
  try {
    const results = await hybridSearch(userMessage, 3);
    if (results.length > 0) {
      brainContext = '\n\nRelevant knowledge from brain:\n' +
        results.map(r => { sources.push({ slug: r.slug, title: r.title }); return `- [${r.title}]: ${r.snippet}`; }).join('\n');
    }
  } catch { /* Search is best-effort */ }

  const messages: ChatMessage[] = [
    { role: 'system', content: SYSTEM_PROMPT + brainContext },
    ...history,
    { role: 'user', content: taskSpec?.enhanced_prompt || userMessage },
  ];

  try {
    const response = await provider.chat(messages);

    // Log activity
    const engine = getBrainEngine();
    await engine.logActivity('chat', { model: provider.name, user: userMessage.slice(0, 100) });

    return { message: response, taskSpec, sources, model: provider.name };
  } catch (err) {
    // Try fallback providers
    for (const fallback of providers) {
      if (fallback.name === provider.name || !fallback.available()) continue;
      try {
        const response = await fallback.chat(messages);
        return { message: response, taskSpec, sources, model: fallback.name };
      } catch { continue; }
    }
    return { message: `Error: ${err instanceof Error ? err.message : 'Unknown error'}`, model: 'error' };
  }
}
