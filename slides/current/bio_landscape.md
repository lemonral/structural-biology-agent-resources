# Biological and structural agents: research landscape

Author: Yi Zhou (周熠). English edition, 14 November 2026. Based on the archived research notes.

## A Research-Role Map of Biological Agents

Nine examples occupy different research roles: frameworks, research systems and software entry points

- **Knowledge / research**: BioChatter; Biomni
- **Analysis / experiment choice**: CellAgent; BioDiscoveryAgent
- **Structure determination**: Phenix AI Agent; CryoNet.Agent; StructAgent
- **Protein engineering**: ProtAgents; Sparks

A representative, overlapping classification rather than an exhaustive map or common autonomy ranking. BioChatter is an application framework. Biomni and CellAgent are research systems. Phenix and CryoNet entries use official implementation or capability documentation, which is not comparable to a shared benchmark protocol.

- https://www.nature.com/articles/s41587-024-02534-3
- https://github.com/snap-stanford/Biomni
- https://arxiv.org/html/2407.09811v1
- https://arxiv.org/abs/2405.17631
- https://www.phenix-online.org/documentation/reference/ai_agent.html
- https://cryonet.ai/agent/
- https://github.com/bhgtiger/StructAgent
- https://pubs.rsc.org/en/content/articlehtml/2024/dd/d4dd00013g
- https://arxiv.org/html/2504.19017v1

## Knowledge, Analysis and Experimental Decisions

These routes change different stages of research and use different kinds of feedback

- **BioChatter: integration framework**: Knowledge graphs, RAG and model/API chains. Integration needs external fact-checking.
- **Biomni: research environment**: Retrieve tools/data, plan and execute code. Public cases do not cover every structural task.
- **CellAgent: analysis workflow**: Plan, execute and evaluate with tool retrieval. Single-cell evidence depends on data and metrics.
- **BioDiscoveryAgent: experiment choice**: Select the next round from perturbation feedback. Data-based evaluation, not wet-lab automation.

Left: BioChatter author-manuscript Fig. 1, snapshot 2024-02-23, preserving its original meaning. The other three systems do not share this diagram. CellAgent follows the 2024 preprint mechanism, without mixing later-version scores. BioDiscoveryAgent illustrates experimental selection, not an instrument-control protocol.

- https://www.nature.com/articles/s41587-024-02534-3
- https://biocypher.github.io/biochatter-paper/
- https://github.com/snap-stanford/Biomni
- https://arxiv.org/html/2407.09811v1
- https://arxiv.org/abs/2405.17631

## Structural Agents: Software and Quality Gates

Scientific engines build, fit and refine models. Agents organize steps, constraints and review

- **Phenix AI Agent**: Crystallography and cryo-EM; LLM analysis and planning Parameter allowlists, stage gates; Official documentation and cases; Bounded by software and data Final structures need expert review
- **CryoNet.Agent**: Workflows for maps, FASTA, models; Typed input catalogue Shared session and job entry; Official catalogue and tutorials; An interface is not a blind test Accept individual tools separately
- **StructAgent**: cryo-EM building and revision; Reasoning with local execution Expert approval for major edits; Cases in the 2026 preprint; Evidence supports bounded tasks Not universal autonomous solving

Phenix documents PERCEIVE, THINK, PLAN, BUILD, VALIDATE and OUTPUT; LLMs mainly participate in THINK and PLAN. CryoNet descriptions use the archived official HTML when live retrieval timed out. StructAgent here is Xiaohu Guo’s cryo-EM system, not the unrelated arXiv:2607.11388 namesake. Cases and product documentation cannot support direct success-rate comparisons.

- https://www.phenix-online.org/documentation/reference/ai_agent.html
- https://cryonet.ai/agent/
- https://www.biorxiv.org/content/10.64898/2026.05.18.725842v1
- https://github.com/bhgtiger/StructAgent

## Protein Engineering: Design and Hypothesis Tests

Generation, prediction, simulation and experimental validation support different levels of evidence

- **ProtAgents**: Group chat coordinates planning and critique. Tools combine generation, prediction and physics.; Computational design and physics examples. Compare collaboration at matched budgets.
- **Sparks**: Generator–reflection pairs organize research. Code and analysis retain or revise hypotheses.; Computational studies of protein properties. Limited by sampling, models and conditions.

Left: original ProtAgents Fig. 1, preserving its meaning, not our architecture. ProtAgents demonstrates computational studies rather than a universal scientific benchmark. Sparks combines generation, prediction, secondary-structure/property models and MD. Surrogate scores or simulations do not establish experimental confirmation. External validation remains necessary.

- https://pubs.rsc.org/en/content/articlehtml/2024/dd/d4dd00013g
- https://arxiv.org/html/2402.04268v1
- https://github.com/lamm-mit/ProtAgents
- https://arxiv.org/html/2504.19017v1
- https://github.com/lamm-mit/Sparks/
