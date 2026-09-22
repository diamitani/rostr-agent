# Jev × ROSTR — how to use it today

Jev is a System One model: unstructured state in, typed probabilistic decisions out. It is not a chat model. Do not replace the CTO agent with it.

## Verdict

| Question | Answer |
| --- | --- |
| Will it work? | Yes on PAL intent, NPAO, allocation, RAG scoring, and gates. No as the agent that writes code. |
| Is it better? | Yes versus the current first-regex-wins compiler and hardcoded 5.5/6.5/7.0 NPAO weights. |
| Does it add value? | Yes. Those calls are the most frequent, cheapest, and most brittle decisions in ROSTR. |
| Use the adapter in prod PAL? | No. `system-one-adapter-python` is an LLM stand-in for evals. |

## Use Jev today

```bash
export TYPESAFE_API_KEY=sk-...
pip install typesafe-sdk
# optional comparison harness
pip install 'system-one-adapter[openai]'
```

```python
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

client = TypeSafeClient(model="jev")  # or jev-latest
result = client.system_one(
    state={"task": "Fix error 500 in chat stream handler"},
    questions={
        "phase": Choice(
            instructions="Which 5D lifecycle phase is this task in?",
            criteria={
                "PreD": "Research / go-no-go",
                "Design": "Specify what to build",
                "Development": "Implement",
                "Deploy": "Ship",
                "Debugging": "Root-cause a defect",
            },
        ),
        "requires_approval": Noul(instructions="Named human approval gate required?"),
    },
)
if result.choices["phase"].confidence < 0.4:
    # escalate semantic enhancement to Claude/Grok
    ...
```

Other wires that already serve Jev:

- Vercel AI Gateway: `base_url=https://ai-gateway.vercel.sh/typesafe`, model `typesafe-ai/jev`
- OpenRouter: `base_url=https://openrouter.ai/api`, model `~typesafe/jev-latest`

## What the adapter is

[system-one-adapter-python](https://github.com/typesafe-ai/system-one-adapter-python) implements the same `system_one` API on OpenAI/Anthropic. Use it to A/B Jev vs GPT vs Claude on identical PAL questions. Using it as production routing reintroduces sequential tokens, malformed JSON, and uncalibrated confidence — the problems System One exists to remove.

```python
from system_one_adapter import SystemOneAdapterClient, Choice

client = SystemOneAdapterClient(structured_outputs=True, llm_answer_mode="probabilities")
client.system_one(state, questions, provider="openai", model="gpt-4o-mini")
```

## Where it sits in ROSTR

Replace: PAL stage 1, NPAO classify/score, agent allocation, RAG DAL credibility/coverage, approval/jailbreak checks.

Keep an LLM: PAL semantic enhancement, specialist generation, tool-calling, writeups.

Unchanged: ContextEngine, Hub persistence.

## Runtime in this repo

`Tools/system_one/` is the decision layer. Resolution order:

1. `TYPESAFE_API_KEY` → Jev
2. `AI_GATEWAY_API_KEY` → Vercel gateway
3. `OPENROUTER_API_KEY` → OpenRouter
4. `ROSTR_SYSTEM_ONE_ADAPTER=1` → LLM adapter (comparison)
5. else local typed engine

```bash
python3 Tools/pydantic_deep_runner.py --compile-only "Research whether we should build a billing refund workflow"
python3 -m unittest Projects/di-cto-agentcore/tests/test_system_one.py
```
