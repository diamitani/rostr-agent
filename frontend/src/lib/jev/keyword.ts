import type { Domain, Phase } from "./types";

/** The current rostr-agent harness: first-regex-wins, hardcoded NPAO weights. */
export function detectPhaseKeyword(prompt: string): { phase: Phase; domain: Domain } {
  const p = prompt.toLowerCase().trim();

  if (/(fix|error|bug|crash|issue|broken|debug|revert|exception|failure)/i.test(p)) {
    return { phase: "Debugging", domain: "code" };
  }
  if (
    /(deploy|release|production rollout|ship to prod|prod release|ci\/cd workflow|github actions)/i.test(p) &&
    !/(build|develop|implement api|scaffold)/i.test(p.split(" ")[0] ?? "")
  ) {
    return { phase: "Deploy", domain: "ops" };
  }
  if (
    /^(design|ux|ui|wireframe|spec|figma|palette|typography)/i.test(p) ||
    (/(design ui|ui component hierarchy|ux specification|design tokens)/i.test(p) &&
      !/(build|implement|code|deploy)/i.test(p.split(" ")[0] ?? ""))
  ) {
    return { phase: "Design", domain: "design" };
  }
  if (/(build|create|implement|code|scaffold|add|make|endpoint|api route|backend|frontend|integration)/i.test(p)) {
    return { phase: "Development", domain: "code" };
  }
  return { phase: "PreD", domain: "research" };
}

export function keywordPriority(phase: Phase) {
  const phaseVal = { Debugging: 10, Deploy: 8, Development: 6, Design: 4, PreD: 2 }[phase];
  const depVal = 5.5;
  const bizVal = 6.5;
  const resVal = 7.0;
  const score = phaseVal * 0.35 + depVal * 0.3 + bizVal * 0.25 + resVal * 0.1;
  return {
    score: Number(score.toFixed(2)),
    formula: `(${phaseVal} × 0.35) + (${depVal} × 0.30) + (${bizVal} × 0.25) + (${resVal} × 0.10)`,
    fakeWeights: { depVal, bizVal, resVal },
  };
}
