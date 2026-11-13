# Current 30-slide presentation: source material

Author: Yi Zhou (周熠). English edition: November 14, 2026. Source deck: November 13, 2026.

[English](README.md) · [Chinese original notes](README.zh-CN.md)

- `content.json`: English titles, content, speaker notes and source links for all 30 slides.
- `build.mjs`: English authoring script using repository-relative assets.
- `agent_methods.md` and `bio_landscape.md`: English method and research-landscape notes.
- `assets/`: original source figures, scientific images and provenance records. Third-party rights remain with the original authors.
- `*.zh-CN.*`: preserved Chinese source files. `build.zh-CN.mjs` reads `content.zh-CN.json`.

Ready-to-use output: [English PPT](../../site/en/brief/structural-biology-agent-30-en.pptx), [slide viewer](../../site/en/brief/index.html), [English slide notes](../../site/en/brief/sources.html), [Chinese PPT](../../site/brief/structbio-agent-landscape-30-20261113.pptx).

## Authoring dependencies

The script uses `@oai/artifact-tool` from the author’s bundled Codex runtime. That runtime is not distributed by this repository or guaranteed to be installable as an ordinary Node dependency. Rebuilding requires that runtime to be available through Node’s module resolution and the **Arial** font. The preserved Chinese script uses Hiragino Sans GB.

In an environment with these dependencies, run `node slides/current/build.mjs`. Output goes to the ignored `slides/current/generated/` directory. Validate package structure and visually review every slide before replacing a published PPT. The authoring script does not overwrite the website’s final presentation.

Reading or serving the static website requires none of these authoring dependencies.
