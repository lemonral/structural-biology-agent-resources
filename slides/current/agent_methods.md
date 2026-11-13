# 通用Agent背景：六种机制与三页讲述方案

核验日期：2026-11-13。资料来源限定原论文、作者项目站/代码、框架官方文档。下列原论文实验均不构成结构生物学有效性证明。无需搬用跨论文性能百分比。

## 1. 先建立六个设计维度，而非论文名称清单

| 机制 | 改变系统哪一层 | 原研究中的机制与实验场景 | 对本项目的设计启示与边界 |
|---|---|---|---|
| **ReAct** | 单次任务的行动反馈 | 推理/计划与环境行动交替，观察影响下一步；原实验含HotpotQA、FEVER、ALFWorld、WebShop | 在结构任务中保存动作、观察和可审计决策摘要。检索结果或工具输出错误时，闭环仍可能沿错误证据继续。结构对象与科学判据需另加。 |
| **LLMCompiler** | 任务依赖与执行调度 | Planner生成带依赖的调用计划，Task Fetching Unit分派就绪任务，Executor执行；官方仓库复现HotpotQA、Movie Recommendation、ParallelQA | 已知共享输入后的独立分析可并行。并行度受真实依赖、资源和外部服务限制，错误依赖不能靠调度器自动修复。 |
| **Reflexion** | 跨尝试的经验记忆 | 将反馈总结为反思文本，存入episodic memory影响后续尝试，**不必更新模型权重**；原研究含决策、问答与代码任务 | 可复用经验证的故障修复经验。反思只是文字假设，必须核验反馈来源及适用条件，不能把反思当作独立科学评分。 |
| **LATS** | 搜索与推断预算 | 将MCTS、语言模型价值评价与反思结合，探索多个行动轨迹；原研究覆盖编程、交互问答、网页任务及推理 | 可用于少量候选路径的预算内探索。对昂贵GPU/HPC任务，分支执行成本与评价可信度是先决条件，不能照搬文本任务的搜索收益。 |
| **DSPy** | 离线程序/提示优化 | 用声明式模块和签名描述LM程序，按数据与指定metric优化程序参数；原论文含数学、多跳检索、复杂问答和Agent循环 | 可优化任务解析、工具选择和报告依据检查。需要开发/验证划分与可信metric；优化代理评分并不自动保证科学质量。 |
| **AutoGen** | 角色、通信与协作 | 可配置的会话Agent组合LLM、人类和工具，按消息与对话策略协作；原研究示例含数学、代码、问答和决策等 | 可把规划、工具执行、质控分配给角色，但同源模型的互相同意不等于独立验证。协调、上下文与工具预算须和单主控比较。 |

表中“对本项目”一列是设计推论；其中风险判断是本项目工程分析，不写成原论文已完成结构生物学对照实验。

### 原始来源与官方代码

1. ReAct（2022 preprint / ICLR 2023）：https://arxiv.org/abs/2210.03629 ；作者站 https://react-lm.github.io/ 。作者站明确给出ALFWorld失败例，并说明prompting的上下文与学习支持限制。
2. LLMCompiler（2023 preprint / ICML 2024）：https://arxiv.org/abs/2312.04511 ；https://github.com/SqueezeAILab/LLMCompiler 。官方仓库给出三组件与三个benchmark入口。
3. Reflexion（NeurIPS 2023）：https://arxiv.org/abs/2303.11366 ；https://github.com/noahshinn/reflexion 。反思使用语言反馈与经验缓冲，并非传统参数更新式RL。
4. LATS（2023 preprint / ICML 2024）：https://arxiv.org/abs/2310.04406 ；当前官方仓库 https://github.com/andyz245/LanguageAgentTreeSearch （旧作者仓库lapisrocks重定向至此）。
5. DSPy（2023 preprint / ICLR 2024）：https://arxiv.org/abs/2310.03714 ；https://github.com/stanfordnlp/dspy ；当前官方文档 https://dspy.ai/current/ 。原论文能力与当前API分开介绍，避免拿旧代码当当前接口。
6. AutoGen（2023 preprint / COLM 2024）：https://arxiv.org/abs/2308.08155 ；Microsoft原论文PDF https://www.microsoft.com/en-us/research/wp-content/uploads/2023/08/LLM_agent.pdf 。不把论文机制与所有当前SDK版本的API等同。

## 2. 推荐新增三页背景（可根据全篇篇幅并为两页）

### 页A：Agent方法谱系：反馈、计划、记忆、搜索、优化与协作

**核心句**：这些方法改变Agent的不同部位，可以组合使用，不构成统一的优劣排行榜。

建议主视觉为可编辑“系统部件地图”，不用6行文字卡片：

- 中轴：任务与上下文 / 规划决策 / 动作执行 / 外部观察。
- ReAct标在决策–行动–观察的单次反馈回路。
- LLMCompiler标在计划展开为DAG及就绪调度处。
- Reflexion标在观察写入跨次经验、下次取回处。
- LATS标在规划器展开多个候选轨迹、评价回传处。
- DSPy放在外侧离线“数据 + metric + optimizer”边界，对程序参数进行优化。
- AutoGen放在角色通信层，强调它是组织方式，并不替代上述每项机制。

**底部结论**：本项目先实现统一状态与真实工具闭环，再按失败类型和预算引入搜索、经验优化或协作。

**衔接**：它们到底改变了怎样的执行方式？用逐步反馈和依赖编排作具体比较。

### 页B：行动反馈与依赖编排是两种互补控制方式

**核心句**：ReAct适应执行中出现的新信息，LLMCompiler利用已知依赖中的并行机会。

主视觉为两个可编辑技术图，使用同一个结构任务解释，勿用无关网页示例替代本项目语义：

左半“逐步反馈”：
输入检查 → 发现多链 → 澄清目标链 → 选择分析工具 → 读取结果 → 调整后续动作。
标出每轮动作依赖新观察。

右半“依赖图”：
冻结对象与预处理产物 → 分支A（域几何）及分支B（界面接触）→ 等待就绪 → 联合验证。
在A/B边上写明传递的是同一版本的预处理产物引用。

下方采用一行取舍：
- 需要澄清/候选动态变化：允许反馈决策。
- 输入和依赖已明确：优先固定DAG、并行与可复算执行。
- 新结果改变科学意图：重新确认任务规格。

**备注中的准确边界**：两个图是将原方法机制映射到本项目的解释图，并非原论文的结构生物学实测案例。LLMCompiler降低延迟的原研究结果依赖具体任务与模型，不能直接写为本项目加速倍数。

### 页C：方法选择由反馈可信度、成本和可验证性决定

**核心句**：先识别任务的决策结构，再决定增加哪种Agent机制。

推荐“取舍坐标图 + 条件说明”，而不是再次放六方法大表：

横轴：可预先确定的依赖程度（低→高）；纵轴：单次行动与错误代价（低→高）。图上位置是定性架构分析，不能表示实测排名。

- 已明确且可重复的科学步骤：固定工作流 + 类型和质量检查。
- 未知对象/动态候选：ReAct式反馈 + 澄清与停止条件。
- 独立分支多：DAG调度；资源与I/O约束决定可并行程度。
- 需要探索多条路线：LATS类搜索，但先确定可信评分与总预算。
- 可重复故障：Reflexion类经验，采用前核验反馈与版本。
- 有标注任务与稳定指标：DSPy类离线优化，冻结最终测试集。
- 有真实分工需求：多Agent组织，与相同工具/预算的单主控对照。

**本项目选型结论**：单主控Agent + 持久状态图 + 类型化工具 + 外部科学验证作为基本形态；其他机制作为可检验扩展。

## 3. 从研究机制到工程框架的连接

论文回答机制是否在特定基准上有效；框架提供状态、工具、运行和集成组件；协议只规定互操作边界，三者不能互相替代。LangGraph官方区分预定执行路径的workflow与动态过程/工具使用的agent，且允许在同一图中组合二者。当前LangChain官方栈还区分Deep Agents、LangChain和LangGraph，但无需在30页里把每个SDK展开成一章。

Primary docs：
- https://docs.langchain.com/oss/python/langgraph/workflows-agents
- https://www.langchain.com/oss-overview

此处为框架职责说明，不使用“框架自动保障结构质量”之类断言。结构对象、单位、坐标、采样与独立科学判据仍由项目实现。

## 4. 已准备的作者原图

- `research/assets/react_official_diagram.png`：198,664 bytes；来源 https://react-lm.github.io/files/diagram.png ，作者站的机制比较图，原始下载未修改。适合用作论文机制图或背景对照，中文解读放在旁边。
- `research/assets/agent_figure_sources.json`：记录来源、字节和SHA256。
- LLMCompiler作者仓库仅有`figs/thumbnail.png`，直连raw.githubusercontent下载SSL超时；未把不存在的文件当作可用资产。Native依赖图已足够，若再次下载可用 https://raw.githubusercontent.com/SqueezeAILab/LLMCompiler/main/figs/thumbnail.png 。

