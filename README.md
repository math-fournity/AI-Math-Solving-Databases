# AI-Math-Solving-Databases

AI 数学竞赛题解题系统的**数据表整体导出**与题库目录。包含系统全生命周期使用的三个
ArangoDB 库的全部数据表（JSONL 导出 + sha256 manifest + 一键恢复脚本），以及系统
题源所用开源数据集的目录索引（只给 URL，不重复上传题目本身）。

> 仓库分工：系统代码与架构见
> [AI-Math-Competition-Problem-Solving-System](https://github.com/math-fournity/AI-Math-Competition-Problem-Solving-System)；
> 每题运行现场见
> [AI-Math-Solving-Trajectories](https://github.com/math-fournity/AI-Math-Solving-Trajectories)
> 与 [AI-Math-Solving-Trajectories-Archive](https://github.com/math-fournity/AI-Math-Solving-Trajectories-Archive)；
> 早期管线代码见
> [AI-Math-Normal-Solver](https://github.com/math-fournity/AI-Math-Normal-Solver)。

## 内容结构

```
dumps/
  manifest.json                      三库全部数据表清单：docs 数/文件/sha256/是否 gzip
  xishujuzhen_math_glm52/            当前系统主库（79 张表）
  xishujuzhen_math/                  早期数学认知世代库（31 张表，含 23.9 万篇 arXiv 论文元数据）
  p27sim/                            全流程模拟专用库（6 张表，与生产键空间隔离）
problem-bank-catalogs/               题库目录（开源数据集索引元数据）
scripts/restore_arangodb_dump.py     恢复脚本
```

## 数据表概览

### `xishujuzhen_math_glm52` —— 当前系统主库（与早期平凡解题系统共享）

| 数据表 | 文档数 | 内容 |
|---|---|---|
| `p27_continuation_runs` | 10,072 | p27 续传管线每题运行记录（rounds_log/终态/并发窗口） |
| `p27_continuation_events` / `p27_sessions` / `p27_continuation_results` | 1,125 / 2,131 / 192 | 事件流水 / 会话注册表 / 终态收集 |
| `p27_monitor_alerts` / `monitor_alerts` / `pipe_monitor_alerts` | 62,689 / 286 / 315 | 监控 alert 全量记录 |
| `devin_problem_runs` | 50,552 | 早期平凡解题系统每题运行记录 |
| `problem_extraction_progress` | 2,460,311 | 题库提取进度 + **全部题目/解答本体**（全字段导出，problem_text/solution_text 含 98.5%/98.4% 文档；另有 problem_hash/external_ref 供上游对账） |
| `problem_profiles` / `patterns` | 456 / 2,820 | 题目画像与模式库 |
| `selection_*` / `analysis_*` / `analysis_events` | 1,453+ / 8,473+ / 40,909 | 选题批次与分析批次 |
| `audit_runs` / `audit_results` / `p27_proof_audit_runs` / `p27_proof_audits` | 1,534 / 1,397 / 141 / 14 | proof 审计全链 |
| `math_manify_run_records*` | 1,299 + 4×3 | math-manify 立项方法论运行记录 |
| `math_datasets` | 10,063 | 题库数据集目录（与 problem-bank-catalogs 同源） |
| 其余 60+ 张 | — | 批次/计数器/步进门闸/知识图谱节点边等 |

### `xishujuzhen_math` —— 早期数学认知世代

`solutions`（159 条解题记录）、`problems`（60 题）、`ut_nodes/ut_edges/dg_nodes/dg_edges`
（推导/依赖图 ~6,100 节点边）、`cognition_units/cog_versions`（认知单元）、
`arxiv_papers`（239,472 篇论文元数据，gzip 导出 107MB）等 31 张表。

### `p27sim` —— 全流程模拟库

模拟系统（`src/sim`，ARANGO_DB 自动覆盖为 p27sim）的 6 张表：模拟 batches/runs/
sessions/events/results/step_gates。

## 恢复方法

```bash
pip install python-arango
python scripts/restore_arangodb_dump.py --host http://localhost:8529 \
    --user root --password <密码>          # 默认恢复全部三库
# 可选：--databases p27sim 只恢复单库；--dry-run 只校验
```

脚本按 manifest 校验 sha256，重建库与表，`import_bulk` 批量导入（保留原 `_key`，
`_rev` 由服务器重新生成）。每张表的文档数与导出文件一一对应，可用 manifest 复核完整性。

## 敏感性说明

- 数据表为解题系统的程序运行记录（题目 ID、状态机字段、终态分类、审计结论等），
  不含 API 密钥/凭据/密码。
- 公开化处理：表中字段出现的本地目录名（工作环境路径）已统一替换为中性名称，其余
  内容未改动。
- 未纳入本仓库的库：`email_project`（含密钥材料，敏感）、`xops`、`grove_math`、
  `proofs_in_ai_studio`、`xishujuzhen`（知识图谱世代，非解题数据表）。

## 题库（开源，只给 URL）

系统题源均为公开数据集，本仓库 `problem-bank-catalogs/` 提供完整索引元数据（10,063 个
数据集的 URL/tier/题量/许可字段），题目本体请从上游获取：

- Omni-MATH: https://huggingface.co/datasets/KbsdJames/Omni-MATH
- DeepMath-103K: https://huggingface.co/datasets/zwhe99/DeepMath-103K
- AMO-Bench: https://github.com/meituan-longcat/AMO-Bench
- AIME: https://huggingface.co/datasets/math-ai/aime24 · [aime25](https://huggingface.co/datasets/math-ai/aime25) · [aime26](https://huggingface.co/datasets/math-ai/aime26)
- MathArena: https://matharena.ai/ · https://huggingface.co/datasets/MathArena
- ODA-Math-460k: https://huggingface.co/datasets/OpenDataArena/ODA-Math-460k

- MathArena: https://matharena.ai/ · https://huggingface.co/datasets/MathArena
- ODA-Math-460k: https://huggingface.co/datasets/OpenDataArena/ODA-Math-460k

## 题目指向解析指南（problem_id → 原始题目）

**题目与解答本体已全量在本仓库数据表内**（`problem_extraction_progress` 全字段导出，含
`problem_text`/`solution_text`），恢复数据库即得完整题库，无需回上游。本节用于**对账上游**
（确认题目版本、追溯来源）。

### 1. problem_id 命名约定 → 上游数据集

`problem_id`（或 run 目录名、表名中的题目段）格式为 `<数据集前缀>_<题内序号或ID>`：

| ID 前缀 | 上游数据集 | 定位方法 |
|---|---|---|
| `deepmath_103k_00000764` | DeepMath-103K | 上游按行组织，取 ID 尾号对应行 |
| `omni_math_004100` | Omni-MATH | 取 problem 4100 |
| `amo_bench_00000006` | AMO-Bench | 取第 6 题（共 50 题） |
| `aime_2024_0009` | AIME 2024 | 第 9 题 |
| `oda_math_460k_00007019` | ODA-Math-460k | 取第 7019 行 |
| `imo2009p6` / `compfiles_imo1993p3` | IMO 官方历年题（IMO 2009 P6 / IMO 1993 P3） | 按 `imo<年份>p<题号>` 直读，公开文本随处可得 |
| `mathnet_001631` / `fate_000329` / `polymath_01687` | 对应 HF 数据集（见 problem-bank-catalogs 索引按 repo_id 检索） | 按 ID 尾数定位行 |
| `matharena/*` | MathArena 竞赛评测集 | 见上方 MathArena URL |

### 2. 引用字段与一致性校验

`problem_extraction_progress` / `problem_entries` / `problem_profiles` 等表每行携带：

- `source_dataset` / `external_ref`：来源数据集与上游定位引用；
- `problem_hash`：题目文本的内容哈希——从上游取回题目后可**哈希比对验证是否为同一题**
  （上游数据更新/行序变化时以哈希为准）；
- `difficulty_tier` / `priority`：分层与优先级。

### 3. 实际题面文本在哪里

做过解题的题目，**题面全文已随运行现场上传**（解题可复现性所需）：

- 当前世代：`AI-Math-Solving-Trajectories` 的 `p27-workdirs/<run>/problem.txt`（题面原文）；
- 早期世代：`AI-Math-Solving-Trajectories-Archive` 的 `workdirs/<run>/`（`prompt.txt` 内嵌题面）
  与 `runs/<run>/exports/conversation.json`（首条用户消息含题面）。

因此：**凡是系统实际做过的题，无需回溯上游即可看到完整题面**；只有"提取了但从未运行"
的题（多数为大规模数据集行）需按上表回溯上游获取。

### 4. 已知限制

- 上游数据集可能更新行序或版本——本仓库快照为导出时点版本，以 `problem_hash` 与上游比对可识别差异。
- 从零复原完整工作环境（含本仓库数据）的步骤见主 repo
  [docs/RESTORE-GUIDE.md](https://github.com/math-fournity/AI-Math-Competition-Problem-Solving-System/blob/main/docs/RESTORE-GUIDE.md)。

## Data Licensing（数据许可）

- 仓库中的**脚本与文档**为 MIT（见 LICENSE）。
- **题目与解答数据**来自各上游开源数据集，再分发遵循其原始许可：
  Omni-MATH = Apache-2.0；ODA-Math-460k = CC-BY-NC-4.0（非商业）；DeepMath-103K 及其余
  数据集的许可以上游页面为准（`problem-bank-catalogs/` 目录的 `license` 字段有记录，为 null 者
  请查上游 repo）。本仓库族为**非商业研究归档**用途，使用数据请遵守对应上游许可并署名。

## License

MIT License，见 [LICENSE](LICENSE)。
