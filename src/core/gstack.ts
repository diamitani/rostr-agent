// ============================================================
// ROSTR — gStack (Skill Library & Plugin System)
// ============================================================

import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'fs';
import { join } from 'path';
import { parse } from 'yaml'; // We'll need a simple YAML parser or use regex if we don't want deps

export interface Skill {
  name: string;
  description: string;
  triggers: string[];
  workflow: string[];
  constraints: string[];
  mcp_tools?: Array<{
    name: string;
    description: string;
    parameters: Record<string, any>;
  }>;
  raw_source?: string;
  provider?: string; // 'claude', 'antigravity', 'codex', etc.
}

export class GStack {
  private libraryPath: string;
  private skills: Map<string, Skill> = new Map();

  constructor(libraryPath?: string) {
    this.libraryPath = libraryPath || join(process.cwd(), 'skills', 'library');
    this.ensureLibrary();
  }

  private ensureLibrary() {
    if (!existsSync(this.libraryPath)) {
      mkdirSync(this.libraryPath, { recursive: true });
    }
  }

  async loadLibrary(): Promise<void> {
    if (!existsSync(this.libraryPath)) return;

    const files = readdirSync(this.libraryPath);
    for (const file of files) {
      if (file.endsWith('.md') || file.endsWith('.json')) {
        try {
          const content = readFileSync(join(this.libraryPath, file), 'utf-8');
          const skill = this.parseSkill(content, file);
          if (skill) {
            this.skills.set(skill.name.toLowerCase(), skill);
          }
        } catch (err) {
          console.error(`Failed to load skill ${file}:`, err);
        }
      }
    }
  }

  private parseSkill(content: string, filename: string): Skill | null {
    // Simple markdown frontmatter parser
    if (filename.endsWith('.json')) {
      return JSON.parse(content) as Skill;
    }

    const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (!frontmatterMatch) return null;

    // Use regex for basic YAML-ish parsing to avoid extra deps if possible
    // But for robustness, we should use a YAML parser if we have one.
    // Since this is a new project, let's assume we can add 'yaml' to package.json later if needed.
    // For now, let's do a basic extraction.
    
    const lines = frontmatterMatch[1].split('\n');
    const data: any = {};
    lines.forEach(line => {
      const [key, ...val] = line.split(':');
      if (key && val) {
        const value = val.join(':').trim();
        if (value.startsWith('[') && value.endsWith(']')) {
          data[key.trim()] = value.slice(1, -1).split(',').map(s => s.trim().replace(/^["']|["']$/g, ''));
        } else {
          data[key.trim()] = value;
        }
      }
    });

    return {
      name: data.name || filename.replace('.md', ''),
      description: data.description || '',
      triggers: data.triggers || [],
      workflow: [], // To be extracted from markdown body
      constraints: data.constraints || [],
      raw_source: content
    };
  }

  /**
   * Converts a raw skill from other platforms (Claude, Antigravity, etc.)
   * into a ROSTR-compatible skill using PAL logic.
   */
  async convertSkill(source: string, provider: string): Promise<Skill> {
    // This is where we use the "applicable" conversion logic.
    // In a real scenario, this might call an LLM via PAL to reformulate the skill.
    // For now, we'll use a template-based approach.

    const nameMatch = source.match(/# (.*)/) || source.match(/name: (.*)/);
    const name = nameMatch ? nameMatch[1].trim() : 'imported-skill';

    const skill: Skill = {
      name: name.toLowerCase().replace(/\s+/g, '-'),
      description: `Imported ${provider} skill: ${name}`,
      triggers: [],
      workflow: [],
      constraints: [],
      provider,
      raw_source: source
    };

    // Use regex to find triggers, tasks, or workflows
    const triggers = source.match(/triggers?:\s*\[?([^\]\n]+)\]?/i);
    if (triggers) {
      skill.triggers = triggers[1].split(',').map(s => s.trim().replace(/^["']|["']$/g, ''));
    }

    // Save to library
    const dest = join(this.libraryPath, `${skill.name}.json`);
    writeFileSync(dest, JSON.stringify(skill, null, 2));
    this.skills.set(skill.name, skill);

    return skill;
  }

  findMatchingSkill(input: string): Skill | null {
    const lowerInput = input.toLowerCase();
    for (const skill of this.skills.values()) {
      if (skill.triggers.some(t => lowerInput.includes(t.toLowerCase()))) {
        return skill;
      }
    }
    return null;
  }

  getSkill(name: string): Skill | undefined {
    return this.skills.get(name.toLowerCase());
  }

  listSkills(): Skill[] {
    return Array.from(this.skills.values());
  }
}

let _gstack: GStack | null = null;
export function getGStack(): GStack {
  if (!_gstack) {
    _gstack = new GStack();
  }
  return _gstack;
}
