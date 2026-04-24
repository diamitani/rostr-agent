import { compilePAL } from '../src/agents/pal.js';

async function test() {
  console.log("Testing PAL with gStack skill match...");
  const spec = await compilePAL("Please deploy to vercel right now");
  console.log("\n--- Task Spec ---");
  console.log(`Matched Skill: ${spec.matched_skill}`);
  console.log(`Constraints: ${spec.constraints.join(', ')}`);
  console.log(`Enhanced Prompt Snippet: ${spec.enhanced_prompt.slice(-200)}`);
}

test();
