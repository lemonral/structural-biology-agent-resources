# 当前30页PPT的内容源

作者：周熠。版本：2026-11-13。

- `content.json`：30页标题、内容、讲稿备注和来源链接。
- `agent_methods.md`、`bio_landscape.md`：Agent方法和九个领域代表系统的研究说明。
- `assets/`：作者原图、来源记录及演示使用的科研图片。图片权利归各原作者。
- `build.mjs`：本版PPT的作者脚本，所有本地素材已改成仓库相对路径。

可直接使用的成品位于 [`site/brief/`](../../site/brief/structbio-agent-landscape-30-20261113.pptx)。

脚本使用作者环境中的 `@oai/artifact-tool`（Codex随附运行时），它不是本仓库提供的通用安装依赖。复用该脚本需要可访问这一运行时，且安装 `Hiragino Sans GB` 字体；本仓库不承诺普通Node环境能直接重新生成PPT。静态网站预览不需要这些依赖。

在具备作者运行时的环境下运行 `node slides/current/build.mjs`，产物写入 `slides/current/generated/`。成品发布时另做版面与包结构验证；生成脚本不会自动覆盖网站成品。
