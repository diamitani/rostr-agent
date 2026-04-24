#!/usr/bin/env node
// ============================================================
// ROSTR Agent Framework — CLI
// ============================================================

import { Command } from 'commander';
import chalk from 'chalk';
import { config } from 'dotenv';
import { existsSync, copyFileSync, mkdirSync } from 'fs';
import { join } from 'path';

// Load .env
config();

const program = new Command();
const gold = chalk.hex('#D4AF37');
const dim = chalk.gray;

const BANNER = `
  ${gold('██████╗  ██████╗ ███████╗████████╗██████╗ ')}
  ${gold('██╔══██╗██╔═══██╗██╔════╝╚══██╔══╝██╔══██╗')}
  ${gold('██████╔╝██║   ██║███████╗   ██║   ██████╔╝')}
  ${gold('██╔══██╗██║   ██║╚════██║   ██║   ██╔══██╗')}
  ${gold('██║  ██║╚██████╔╝███████║   ██║   ██║  ██║')}
  ${gold('╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝')}
  ${dim('Agent OS — Open Source Framework')}
`;

program
  .name('rostr')
  .description('ROSTR Agent Framework — AI Agent OS')
  .version('0.1.0');

// ── INIT ────────────────────────────────────────────────
program
  .command('init')
  .description('Initialize ROSTR brain and configuration')
  .action(async () => {
    console.log(BANNER);
    console.log(gold('  Initializing ROSTR...\n'));

    // Create .env if not exists
    const envPath = join(process.cwd(), '.env');
    const envExample = join(process.cwd(), '.env.example');
    if (!existsSync(envPath) && existsSync(envExample)) {
      copyFileSync(envExample, envPath);
      console.log(chalk.green('  ✓ Created .env from .env.example'));
    }

    // Initialize brain
    const { getBrainEngine } = await import('../core/engine.js');
    const engine = getBrainEngine();
    await engine.init();
    console.log(chalk.green('  ✓ Brain initialized (PGLite)'));

    const stats = await engine.getStats();
    console.log(dim(`    ${stats.total_pages} pages, ${stats.total_embeddings} embeddings`));

    // Check for API keys
    const { listProviders } = await import('../agents/runtime.js');
    const providers = listProviders();
    const available = providers.filter(p => p.available);
    if (available.length > 0) {
      console.log(chalk.green(`  ✓ LLM providers: ${available.map(p => p.name).join(', ')}`));
    } else {
      console.log(chalk.yellow('  ⚠ No LLM API keys configured. Add keys to .env'));
    }

    console.log(`\n${gold('  ROSTR is ready!')}`);
    console.log(dim('  Run: rostr serve    — Start gateway + dashboard'));
    console.log(dim('  Run: rostr chat     — Chat with agent'));
    console.log(dim('  Run: rostr doctor   — Health check\n'));
  });

// ── SERVE ───────────────────────────────────────────────
program
  .command('serve')
  .description('Start ROSTR gateway server')
  .option('-p, --port <port>', 'Gateway port', '3001')
  .action(async (opts) => {
    console.log(BANNER);
    const { startGateway } = await import('../gateway/server.js');
    await startGateway(parseInt(opts.port));
  });

// ── CHAT ────────────────────────────────────────────────
program
  .command('chat [message]')
  .description('Chat with the ROSTR agent')
  .option('-i, --interactive', 'Interactive REPL mode')
  .action(async (message, opts) => {
    const { getBrainEngine } = await import('../core/engine.js');
    const engine = getBrainEngine();
    await engine.init();

    const { chat: agentChat } = await import('../agents/runtime.js');

    if (opts.interactive || !message) {
      // Interactive mode
      const readline = await import('readline');
      const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

      console.log(BANNER);
      console.log(gold('  Interactive chat. Type "exit" to quit.\n'));

      const history: Array<{ role: 'user' | 'assistant'; content: string }> = [];

      const ask = () => {
        rl.question(chalk.cyan('  you › '), async (input) => {
          if (!input || input.toLowerCase() === 'exit') {
            console.log(dim('\n  Goodbye!\n'));
            rl.close();
            process.exit(0);
          }

          history.push({ role: 'user', content: input });
          const result = await agentChat(input, history.slice(-10));
          history.push({ role: 'assistant', content: result.message });

          console.log(gold(`\n  rostr › `) + result.message);
          if (result.sources?.length) {
            console.log(dim(`  sources: ${result.sources.map(s => s.title).join(', ')}`));
          }
          console.log(dim(`  [${result.model}]\n`));
          ask();
        });
      };
      ask();
    } else {
      const result = await agentChat(message);
      console.log(result.message);
      if (result.sources?.length) {
        console.log(dim(`\nSources: ${result.sources.map(s => s.title).join(', ')}`));
      }
      process.exit(0);
    }
  });

// ── SEARCH ──────────────────────────────────────────────
program
  .command('search <query>')
  .description('Search the knowledge brain')
  .option('-l, --limit <n>', 'Max results', '10')
  .action(async (query, opts) => {
    const { getBrainEngine } = await import('../core/engine.js');
    await getBrainEngine().init();

    const { hybridSearch } = await import('../core/search.js');
    const results = await hybridSearch(query, parseInt(opts.limit));

    if (results.length === 0) {
      console.log(dim('No results found.'));
    } else {
      console.log(gold(`\n${results.length} results:\n`));
      for (const r of results) {
        console.log(`  ${chalk.white(r.title)} ${dim(`(${r.type})`)} ${dim(`score: ${r.score}`)}`);
        console.log(dim(`    ${r.snippet.slice(0, 120)}...`));
        console.log();
      }
    }
    process.exit(0);
  });

// ── TASK ────────────────────────────────────────────────
const taskCmd = program.command('task').description('NPAO task management');

taskCmd
  .command('add <title>')
  .description('Add a task (auto-classified with NPAO)')
  .option('-d, --description <desc>', 'Task description')
  .action(async (title, opts) => {
    const { getBrainEngine } = await import('../core/engine.js');
    await getBrainEngine().init();
    const { createTask, NPAO_LABELS } = await import('../agents/npao.js');
    const task = await createTask(title, opts.description);
    const label = NPAO_LABELS[task.npao_category];
    console.log(gold(`\n✓ Task created: ${task.id}`));
    console.log(`  NPAO: ${label.label} (${label.signal})`);
    console.log(`  Phase: ${task.phase}`);
    console.log(`  Priority: ${task.priority_score}\n`);
    process.exit(0);
  });

taskCmd
  .command('list')
  .description('List tasks in NPAO execution order')
  .option('-s, --status <status>', 'Filter by status')
  .action(async (opts) => {
    const { getBrainEngine } = await import('../core/engine.js');
    await getBrainEngine().init();
    const { listTasks, NPAO_LABELS } = await import('../agents/npao.js');
    const tasks = await listTasks(opts.status);

    if (tasks.length === 0) {
      console.log(dim('No tasks found.'));
    } else {
      console.log(gold(`\n${tasks.length} tasks (NPAO order):\n`));
      for (const t of tasks) {
        const label = NPAO_LABELS[t.npao_category];
        const statusIcon = t.status === 'done' ? '✅' : t.status === 'in_progress' ? '🔄' : t.status === 'blocked' ? '🚫' : '○';
        console.log(`  ${statusIcon} [${label.label}] ${t.title} ${dim(`(${t.phase} • ${t.priority_score})`)}`);
      }
      console.log();
    }
    process.exit(0);
  });

taskCmd
  .command('done <id>')
  .description('Mark a task as done')
  .action(async (id) => {
    const { getBrainEngine } = await import('../core/engine.js');
    await getBrainEngine().init();
    const { updateTask } = await import('../agents/npao.js');
    const task = await updateTask(id, { status: 'done' });
    if (task) console.log(chalk.green(`✓ Task ${id} completed: ${task.title}`));
    else console.log(chalk.red(`Task ${id} not found.`));
    process.exit(0);
  });

// ── CONTEXT ─────────────────────────────────────────────
const ctxCmd = program.command('context').description('ContextEngine memory');

ctxCmd
  .command('flash')
  .description('Load recent context (context flash)')
  .action(async () => {
    const { getBrainEngine } = await import('../core/engine.js');
    await getBrainEngine().init();
    const { retrieveContext } = await import('../agents/context-engine.js');
    const ctx = await retrieveContext();

    console.log(gold('\n📋 Context Flash\n'));
    console.log(chalk.white(`  Recommended: ${ctx.recommended_start}`));
    if (ctx.last_session) {
      console.log(dim(`  Last session: ${ctx.last_session.session_id}`));
      console.log(dim(`  Summary: ${ctx.last_session.summary}`));
    }
    if (ctx.recent.length > 1) {
      console.log(dim(`\n  Recent sessions: ${ctx.recent.length}`));
    }
    console.log();
    process.exit(0);
  });

ctxCmd
  .command('save')
  .description('Save current session')
  .option('-s, --summary <summary>', 'Session summary')
  .action(async (opts) => {
    const { getBrainEngine } = await import('../core/engine.js');
    await getBrainEngine().init();
    const { cacheSession } = await import('../agents/context-engine.js');
    const session = await cacheSession({ summary: opts.summary || 'Manual save' });
    console.log(chalk.green(`✓ Session cached: ${session.session_id}`));
    process.exit(0);
  });

// ── DOCTOR ──────────────────────────────────────────────
program
  .command('doctor')
  .description('Run health checks')
  .action(async () => {
    console.log(gold('\n🔍 ROSTR Doctor\n'));

    // Check brain
    try {
      const { getBrainEngine } = await import('../core/engine.js');
      const engine = getBrainEngine();
      await engine.init();
      const stats = await engine.getStats();
      console.log(chalk.green(`  ✓ Brain: ${stats.total_pages} pages, ${stats.total_embeddings} embeddings, ${stats.total_links} links`));
    } catch (e) {
      console.log(chalk.red(`  ✗ Brain: ${e}`));
    }

    // Check providers
    const { listProviders } = await import('../agents/runtime.js');
    const providers = listProviders();
    for (const p of providers) {
      if (p.available) console.log(chalk.green(`  ✓ ${p.name}: configured`));
      else console.log(chalk.yellow(`  ○ ${p.name}: not configured`));
    }

    // Check .env
    if (existsSync(join(process.cwd(), '.env'))) {
      console.log(chalk.green('  ✓ .env file exists'));
    } else {
      console.log(chalk.yellow('  ⚠ No .env file — run: rostr init'));
    }

    console.log();
    process.exit(0);
  });

// ── STATS ───────────────────────────────────────────────
program
  .command('stats')
  .description('Show brain statistics')
  .action(async () => {
    const { getBrainEngine } = await import('../core/engine.js');
    const engine = getBrainEngine();
    await engine.init();
    const stats = await engine.getStats();

    console.log(gold('\n📊 Brain Stats\n'));
    console.log(`  Pages:      ${chalk.white(stats.total_pages)}`);
    console.log(`  Embeddings: ${chalk.white(stats.total_embeddings)}`);
    console.log(`  Links:      ${chalk.white(stats.total_links)}`);
    console.log(`  Sessions:   ${chalk.white(stats.total_sessions)}`);
    console.log(`  Tasks:      ${chalk.white(stats.total_tasks)}`);

    if (Object.keys(stats.page_types).length > 0) {
      console.log(dim('\n  Page types:'));
      for (const [type, count] of Object.entries(stats.page_types)) {
        console.log(dim(`    ${type}: ${count}`));
      }
    }
    console.log();
    process.exit(0);
  });

// ── IMPORT ──────────────────────────────────────────────
program
  .command('import <dir>')
  .description('Import markdown files into brain')
  .action(async (dir) => {
    const { getBrainEngine } = await import('../core/engine.js');
    const engine = getBrainEngine();
    await engine.init();

    const { readdirSync, readFileSync, statSync } = await import('fs');
    const { join: pathJoin, basename, extname } = await import('path');
    const { resolve } = await import('path');

    const absDir = resolve(dir);
    let imported = 0;

    function walkDir(d: string) {
      for (const entry of readdirSync(d)) {
        const full = pathJoin(d, entry);
        const stat = statSync(full);
        if (stat.isDirectory()) { walkDir(full); continue; }
        if (extname(entry) !== '.md') continue;

        const content = readFileSync(full, 'utf-8');
        const slug = basename(entry, '.md').toLowerCase().replace(/[^a-z0-9]+/g, '-');
        const title = basename(entry, '.md');

        engine.putPage({ slug, title, content, type: 'note' });
        imported++;
      }
    }

    walkDir(absDir);
    console.log(chalk.green(`✓ Imported ${imported} files from ${absDir}`));
    process.exit(0);
  });

// ── SKILLS (gStack) ─────────────────────────────────────────
const skillCmd = program.command('skill').description('gStack skill library');

skillCmd
  .command('list')
  .description('List all available skills in gStack')
  .action(async () => {
    const { getGStack } = await import('../core/gstack.js');
    const gstack = getGStack();
    await gstack.loadLibrary();
    const skills = gstack.listSkills();

    if (skills.length === 0) {
      console.log(dim('No skills found in library.'));
    } else {
      console.log(gold(`\n${skills.length} skills available:\n`));
      for (const s of skills) {
        console.log(`  ${chalk.white(s.name)} ${dim(`(${s.provider || 'local'})`)}`);
        console.log(dim(`    ${s.description}`));
        if (s.triggers.length > 0) {
          console.log(dim(`    Triggers: ${s.triggers.join(', ')}`));
        }
        console.log();
      }
    }
    process.exit(0);
  });

skillCmd
  .command('import <path>')
  .description('Import and convert a skill from Claude/Antigravity/Codex')
  .option('-p, --provider <name>', 'Source provider name', 'unknown')
  .action(async (path, opts) => {
    const { getGStack } = await import('../core/gstack.js');
    const { readFileSync } = await import('fs');
    const gstack = getGStack();
    
    try {
      const source = readFileSync(path, 'utf-8');
      const skill = await gstack.convertSkill(source, opts.provider);
      console.log(chalk.green(`✓ Skill imported and converted: ${skill.name}`));
      console.log(dim(`  Location: skills/library/${skill.name}.json`));
    } catch (e) {
      console.error(chalk.red(`Failed to import skill: ${e}`));
    }
    process.exit(0);
  });

program.parse();
