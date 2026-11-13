# Agent methods and architecture choices

Author: Yi Zhou (周熠). English edition, 14 November 2026. Based on the archived research notes.

## Agent Foundations: Reasoning, Action, Observation

A model proposes decisions, tools return observations, and a runtime constrains permitted actions

- **Reasoning**: Form candidate plans and decision summaries
- **External actions**: Execute tools and observe actual results
- **Constrained feedback**: Update actions under permission, budget and stopping rules

Original ReAct author diagram: reason-only, act-only and combined reasoning/action. This is a methods illustration, not a structural-biology experiment from this project. Audit actions, observations and decision summaries without requiring disclosure of private model reasoning.

- https://arxiv.org/abs/2210.03629
- https://react-lm.github.io/

## Agent Methods Change Different System Components

Compare mechanisms and assumptions rather than treating papers as a single performance ranking

- **Method**: Component affected; Mechanism and boundary
- **ReAct**: Action-level feedback; Observe after acting. Incorrect observations can still mislead.
- **LLMCompiler**: Planning and scheduling; Dependency DAG and ready calls. Parallelism obeys real constraints.
- **Reflexion**: Memory across attempts; Reuse verbal feedback without necessarily updating weights. Verify it.
- **LATS**: Search over trajectories; Tree search and evaluation need reliable feedback and extra budget.
- **DSPy**: Offline program optimization; Optimize LM programs on development data. Freeze final tests.
- **AutoGen**: Roles and communication; Coordinate models, people and tools. Consensus is not ground truth.

Original evaluations cover QA, code, web and interactive environments. They do not establish performance on this project’s scientific tasks. DSPy is an offline optimization method, not a mandatory online tool-loop stage. Reflexion can reuse verbal experience without updating model weights. Distinguish the AutoGen paper’s mechanism from later SDK versions.

- https://arxiv.org/abs/2210.03629
- https://arxiv.org/abs/2312.04511
- https://arxiv.org/abs/2303.11366
- https://arxiv.org/abs/2310.04406
- https://arxiv.org/abs/2310.03714
- https://arxiv.org/abs/2308.08155

## Workflow, Single Agent or Multiple Agents?

Fixed computation can use explicit paths. Dynamic selection and collaboration need measurable benefits

- **Fixed workflow**: Known inputs and dependencies; Reproducible paths and low control cost. Define branches in advance.
- **Single controller**: Observations can change the next step; One state and budget. Define tool semantics and stopping rules.
- **Multiple agents**: A testable division of responsibilities; Explicit roles add communication, duplicate work and coordination risk.

Conceptual patterns, not a quantitative ranking. Report success, cost, latency, errors and human intervention under matched tools and budgets. Frameworks do not map one-to-one to patterns. LangChain organizes models, tools and middleware. LangGraph supports stateful workflows and agents. ADK provides agent and workflow components. Framework features do not ensure scientific correctness. Start this project with one controller and a persistent state graph; test collaboration as an additional mechanism.

- https://docs.langchain.com/oss/python/langgraph/workflows-agents
- https://arxiv.org/abs/2308.08155
- https://docs.langchain.com/oss/python/langchain/overview
- https://adk.dev/agents/
