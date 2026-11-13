# Structural Biology Computational Agents

**Author: Yi Zhou (周熠)** · English edition: November 14, 2026

[English](README.md) · [中文](README.zh-CN.md)

A research and development library for turning natural-language structural-biology questions into executable workflows with explicit input/output contracts and scientific acceptance criteria.

The English edition includes **80 paper guides, 39 open-source project guides, a 30-slide presentation, a PRD, architecture documentation, an eight-chapter engineering handbook and a development learning path**. The archive also preserves the original Chinese materials and third-party papers.

## Start here

| Resource | Purpose |
| --- | --- |
| [English resource hub](site/en/index.html) | Main reading and development map |
| [English 30-slide PPT](site/en/brief/structural-biology-agent-30-en.pptx) | Agent methods, biological applications, core architecture and experiments |
| [English slide viewer](site/en/brief/index.html) | Contents, keyboard navigation and full-screen presentation |
| [Paper reading guides](site/en/papers/index.html) | Mechanisms, evidence, limitations, implementation lessons and connections |
| [Framework and project guides](site/en/projects/index.html) | Components, runtime/state, deployment, tradeoffs and exercises |
| [Product requirements](site/en/prd/index.html) | Scope, workflows, requirements, acceptance and implementation gates |
| [Architecture](site/en/architecture/index.html) | Cognition, control, scientific execution and evidence management |
| [Engineering handbook](site/en/engineering/index.html) | Contracts, recovery, validation, governance and operations |
| [Development learning path](site/en/learn/index.html) | A progression from reference tools to evaluated agent control |
| [Presentation source](slides/current/README.md) | English content JSON, notes, figures and authoring script |

GitHub displays HTML as source. Clone the repository and run the static server below to read the complete site.

## Preview locally

```bash
git clone git@github.com:lemonral/structural-biology-agent-resources.git
cd structural-biology-agent-resources
python3 -m http.server 8000 --bind 127.0.0.1 --directory site
```

Open **http://127.0.0.1:8000/**. English is the default entry. Use the language link for the Chinese edition.

The website needs no build, database or model API key. Running the scientific tools and agent described in the documents requires a separate implementation or deployment.

## Presentation outline

| Slides | Content |
| --- | --- |
| 1–2 | Title, roadmap and research questions |
| 3–12 | Agent methods, nine biological/structural frameworks and systems, research gaps and hypotheses |
| 13–16 | Open task maps, core system architecture and the agent control loop |
| 17–26 | Specifications, planning, tools, execution, state, validation, scientific examples and deployment |
| 27–30 | Evaluation, optimization, safety and delivery gates |

The current English deck is in `site/en/brief/`. Historical Chinese courses and decks remain under `site/preview/`, `site/brief/` and `site/_汇报材料/` to preserve existing links. Language editions describe the same development baseline, not parallel product versions.

## Repository layout

- `site/en/`: English reading and development materials.
- `site/`: complete static archive, including Chinese originals, PDFs, figures, presentations and teaching artifacts.
- `slides/current/`: current presentation content, notes, authoring scripts and image provenance.
- `scripts/verify.py`: file-integrity check against `site/SHA256SUMS.txt`.
- `MANIFEST.json`: archive counts, language coverage and current presentation hashes.

```bash
python3 scripts/verify.py
```

English guides are editorial translations of the archived research notes. They preserve source versions, evidence boundaries and implementation status. Source verification dates are historical snapshots, not a claim that every project was re-tested for this translation.

This is a research and design archive. Capability maps express intended scope. Published paper cases, teaching implementations, proposed designs and completed experiments should be evaluated separately.

## Sources and rights

Source links appear in reading guides, project pages, slide notes and asset provenance records. Third-party papers, figures and software retain their respective licenses and copyright. See [NOTICE.md](NOTICE.md).
