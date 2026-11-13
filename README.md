# 结构生物学计算 Agent：研究与开发资料

**作者：周熠** · 资料归档日期：2026-11-14

面向将自然语言科研问题转化为可执行、具有输入输出约束的结构生物学计算流程。仓库保存完整静态资料网站，以及当前30页学术PPT的内容源与配图。

## 从哪里开始

| 内容 | 路径 | 用途 |
| --- | --- | --- |
| 总导航 | [site/index.html](site/index.html) | 资料阅读主入口 |
| 当前30页PPT | [下载可编辑PPT](site/brief/structbio-agent-landscape-30-20261113.pptx) | 方法背景、领域进展、核心架构、实现与评估 |
| 在线演示页面 | [site/brief/](site/brief/index.html) | 目录、全屏和逐页演示 |
| 逐页资料与来源 | [site/brief/sources.html](site/brief/sources.html) | 每页要点、说明、论文和项目链接 |
| 当前PRD入口 | [site/prd/](site/prd/index.html) | 开发需求与配套合同 |
| 架构设计 | [site/architecture/](site/architecture/index.html) | Agent设计与模块关系 |
| 工程落地 | [site/engineering/](site/engineering/index.html) | 作业、状态、数据、验证、运维 |
| 开源项目 | [site/projects/](site/projects/index.html) | 框架与项目的分类学习资料 |
| 开发学习路线 | [site/learn/](site/learn/index.html) | 从入门到工程实现 |
| 论文索引 | [site/论文索引.html](site/论文索引.html) | 论文详情与本地原文 |
| 当前PPT内容源 | [slides/current/](slides/current/README.md) | 内容JSON、讲稿备注、研究说明和配图 |

GitHub页面通常显示HTML源码。要浏览完整网站，请先克隆仓库，再启动下方的本地预览服务。

## 本地预览

```bash
git clone git@github.com:lemonral/structural-biology-agent-resources.git
cd structural-biology-agent-resources
python3 -m http.server 8000 --bind 127.0.0.1 --directory site
```

浏览器访问 `http://127.0.0.1:8000/`。网页无需构建，也不需要数据库或模型API密钥。资料所述科学工具和Agent的实际运行需要另外实现或部署。

## 当前PPT结构

| 页码 | 内容 |
| --- | --- |
| 1–2 | 封面、目录与核心问题 |
| 3–12 | 通用Agent方法背景、九个生物学/结构生物学代表框架与系统、研究缺口与定位 |
| 13–16 | 开放任务地图、Agent主架构与内部决策闭环 |
| 17–26 | 任务规格、规划、工具、执行、状态、验证、科研实例和部署 |
| 27–30 | 实验评估、优化、安全与开发路线 |

`site/brief/` 是当前汇报入口。`site/preview/`、`site/_汇报材料/` 等保留以往课程或演示材料，便于沿用旧链接；它们不代表多个并行开发基线。PRD以 `site/prd/` 的当前入口及其说明为准。

## 目录与完整性

- `site/`：完整静态网站、子HTML、PDF、配图、PPT和教学配套文件。保持目录结构，避免相对链接失效。
- `slides/current/`：当前30页PPT的结构化内容和作者资源。重建依赖见该目录说明。
- `scripts/verify.py`：校验站点文件与 `site/SHA256SUMS.txt` 一致。
- `MANIFEST.json`：归档范围、文件数量及当前PPT哈希。

```bash
python3 scripts/verify.py
```

该仓库是资料与设计归档。功能地图描述目标能力，论文案例、教学实现、设计方案与已完成实测结果应分别理解。

## 来源与权利

论文、软件、作者原图和引用材料的来源见各页面及 `slides/current/assets/` 的来源记录。第三方材料遵守各自许可证和版权声明。详见 [NOTICE.md](NOTICE.md)。
