// ============================================================
// ROSTR — Gateway Server (HTTP + WebSocket)
// ============================================================

import express from 'express';
import cors from 'cors';
import { createServer } from 'http';
import { WebSocketServer, WebSocket } from 'ws';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

import { getBrainEngine } from '../core/engine.js';
import { hybridSearch } from '../core/search.js';
import { embedPage, embedAllStale } from '../core/embeddings.js';
import { extractAndSaveLinks, getBacklinks, graphTraversal } from '../core/knowledge-graph.js';
import { chat, listProviders, type ChatMessage } from '../agents/runtime.js';
import { createTask, listTasks, updateTask } from '../agents/npao.js';
import { cacheSession, retrieveContext, generateReport, queryHistory, getSessionCount } from '../agents/context-engine.js';
import { compilePAL } from '../agents/pal.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

export async function startGateway(port = 3001): Promise<void> {
  const app = express();
  app.use(cors());
  app.use(express.json({ limit: '10mb' }));

  // Init brain
  const engine = getBrainEngine();
  await engine.init();

  // ── Health ────────────────────────────────────────────
  app.get('/api/status', async (_req, res) => {
    const stats = await engine.getStats();
    const providers = listProviders();
    res.json({
      status: 'ok',
      agent: process.env.AGENT_NAME || 'ROSTR',
      model: process.env.AGENT_MODEL || 'gpt-4o-mini',
      providers,
      brain: stats,
      uptime: process.uptime(),
    });
  });

  // ── Chat ──────────────────────────────────────────────
  app.post('/api/chat', async (req, res) => {
    const { message, history = [] } = req.body as { message: string; history: ChatMessage[] };
    if (!message) return res.status(400).json({ error: 'message required' });
    const result = await chat(message, history);
    res.json(result);
  });

  // ── PAL Compile ───────────────────────────────────────
  app.post('/api/pal/compile', async (req, res) => {
    const { user_input } = req.body as { user_input: string };
    if (!user_input) return res.status(400).json({ error: 'user_input required' });
    const spec = await compilePAL(user_input);
    res.json(spec);
  });

  // ── Brain Pages ───────────────────────────────────────
  app.get('/api/brain/pages', async (req, res) => {
    const { type, tag, limit } = req.query;
    const pages = await engine.listPages({
      type: type as string, tag: tag as string,
      limit: limit ? parseInt(limit as string) : 50,
    });
    res.json(pages);
  });

  app.get('/api/brain/page/:slug', async (req, res) => {
    const page = await engine.getPage(req.params.slug);
    if (!page) return res.status(404).json({ error: 'not found' });
    const backlinks = await getBacklinks(req.params.slug);
    res.json({ ...page, backlinks });
  });

  app.put('/api/brain/page/:slug', async (req, res) => {
    const { title, content, type, tags } = req.body;
    const page = await engine.putPage({ slug: req.params.slug, title: title || req.params.slug, content, type, tags });
    // Auto-link and embed in background
    extractAndSaveLinks(req.params.slug).catch(() => {});
    embedPage(req.params.slug).catch(() => {});
    res.json(page);
  });

  app.delete('/api/brain/page/:slug', async (req, res) => {
    const ok = await engine.deletePage(req.params.slug);
    res.json({ deleted: ok });
  });

  // ── Search ────────────────────────────────────────────
  app.get('/api/brain/search', async (req, res) => {
    const { q, limit } = req.query;
    if (!q) return res.status(400).json({ error: 'q required' });
    const results = await hybridSearch(q as string, limit ? parseInt(limit as string) : 10);
    res.json(results);
  });

  // ── Knowledge Graph ───────────────────────────────────
  app.get('/api/brain/graph/:slug', async (req, res) => {
    const { type, depth, direction } = req.query;
    const links = await graphTraversal(req.params.slug, {
      type: type as string, depth: depth ? parseInt(depth as string) : 2,
      direction: (direction as 'in' | 'out' | 'both') || 'both',
    });
    res.json(links);
  });

  // ── Tasks (NPAO) ─────────────────────────────────────
  app.get('/api/tasks', async (req, res) => {
    const { status } = req.query;
    const tasks = await listTasks(status as any);
    res.json(tasks);
  });

  app.post('/api/tasks', async (req, res) => {
    const { title, description } = req.body;
    if (!title) return res.status(400).json({ error: 'title required' });
    const task = await createTask(title, description);
    res.json(task);
  });

  app.patch('/api/tasks/:id', async (req, res) => {
    const task = await updateTask(req.params.id, req.body);
    if (!task) return res.status(404).json({ error: 'not found' });
    res.json(task);
  });

  // ── ContextEngine ─────────────────────────────────────
  app.post('/api/context/cache', async (req, res) => {
    const session = await cacheSession(req.body);
    res.json(session);
  });

  app.get('/api/context/flash', async (_req, res) => {
    const ctx = await retrieveContext();
    res.json(ctx);
  });

  app.post('/api/context/search', async (req, res) => {
    const { query } = req.body;
    if (!query) return res.status(400).json({ error: 'query required' });
    const results = await queryHistory(query);
    res.json(results);
  });

  app.get('/api/context/report', async (req, res) => {
    const { since } = req.query;
    const report = await generateReport({ since: since as string });
    res.json({ report });
  });

  // ── Embeddings ────────────────────────────────────────
  app.post('/api/brain/embed', async (_req, res) => {
    const result = await embedAllStale();
    res.json(result);
  });

  // ── Activity ──────────────────────────────────────────
  app.get('/api/activity', async (req, res) => {
    const { limit } = req.query;
    const activity = await engine.getRecentActivity(limit ? parseInt(limit as string) : 20);
    res.json(activity);
  });

  // ── Settings ──────────────────────────────────────────
  app.get('/api/settings', async (_req, res) => {
    res.json({
      agent_name: process.env.AGENT_NAME || 'ROSTR',
      agent_model: process.env.AGENT_MODEL || 'gpt-4o-mini',
      embedding_model: process.env.EMBEDDING_MODEL || 'text-embedding-3-small',
      providers: listProviders(),
    });
  });

  // ── Serve dashboard static files if built ─────────────
  const dashboardDist = join(__dirname, '../../dashboard/out');
  if (existsSync(dashboardDist)) {
    app.use(express.static(dashboardDist));
    app.get('*', (_req, res) => {
      res.sendFile(join(dashboardDist, 'index.html'));
    });
  }

  // ── WebSocket for real-time chat ──────────────────────
  const server = createServer(app);
  const wss = new WebSocketServer({ server, path: '/ws' });

  wss.on('connection', (ws: WebSocket) => {
    const history: ChatMessage[] = [];

    ws.on('message', async (data) => {
      try {
        const msg = JSON.parse(data.toString());
        if (msg.type === 'chat') {
          history.push({ role: 'user', content: msg.message });
          const result = await chat(msg.message, history.slice(-10));
          history.push({ role: 'assistant', content: result.message });

          ws.send(JSON.stringify({
            type: 'response',
            message: result.message,
            model: result.model,
            sources: result.sources,
            taskSpec: result.taskSpec,
          }));
        }
      } catch (err) {
        ws.send(JSON.stringify({ type: 'error', message: String(err) }));
      }
    });
  });

  server.listen(port, () => {
    console.log(`\n  🚀 ROSTR Gateway running on http://localhost:${port}`);
    console.log(`  📡 WebSocket: ws://localhost:${port}/ws`);
    console.log(`  📖 API Docs: http://localhost:${port}/api/status\n`);
  });
}
