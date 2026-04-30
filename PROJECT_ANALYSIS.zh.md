# IKP 项目深度解析

> **[English version: PROJECT_ANALYSIS.md]**
>
> 上游项目：[19PINE-AI/ikp](https://github.com/19PINE-AI/ikp)（位于 `ikp/` 子模块）

---

## 1. 这个项目是做什么的？

**IKP（不可压缩知识探针）** 回答一个问题：**在只能以黑盒方式通过 API 访问某个 LLM 时，该模型到底有多少参数？**

前沿模型厂商（OpenAI、Anthropic、Google 等）通常拒绝公开其部署模型的规模。IKP 提供了一种实证、可复现的方法，仅凭模型自身的知识容量从外部估算其参数量。

**核心洞察：** 事实性知识是不可压缩的。无论如何训练，小模型都无法记住长尾事实。随着参数量增长，模型能可靠回忆的事实数量也随之增加。IKP 利用这一规律构建了七个难度层级的探针。

**核心结论：** R² = 0.917，跨越 89 个开源模型（1.35 亿–1.6 万亿参数）。

---

## 2. 核心方法论

### 七个层级

| 层级 | 网络频率 | 目标参数量 | 示例知识 |
|---|---|---|---|
| T1 | >100K 篇 | 0.1B–1B | 主要国家首都、基础科学 |
| T2 | 10K–100K | 1B–7B | 诺贝尔奖得主、地标高度 |
| T3 | 1K–10K | 7B–70B | 特定历史日期、小众研究者 |
| T4 | 100–1K | 70B–300B | 次要科学家、冷僻技术规格 |
| T5 | 10–100 | 300B–1T | 次要实体细节、出版物元数据 |
| T6 | 2–10 | 1T–5T | 极冷僻研究者、小型研讨会 |
| T7 | ~1 | >5T | 天花板检测、RAG 检测 |

**层级分配：** 对六个递增规模的地标模型（Qwen 2.5 0.5B → Gemini 3.1 Pro）进行实证测试。探针属于第 k 层，当且仅当第 k 个地标模型是能正确回答的最小模型。

### 校准曲线

```
log10(params_B) = 6.790 × 惩罚性准确率 − 0.899
```

- R² = 0.917  ·  LOO 中位数折叠误差 1.59×  ·  68.5% 在 2× 以内  ·  87.6% 在 3× 以内
- **MoE 模型：** 总参数量（R²=0.79）远优于活跃参数量（R²=0.51）

### 评分

- 每探针 3 种表述方式，取最优
- 裁判：Gemini 3 Flash Preview（OpenRouter）
- 惩罚性：`tier_score = max(0, (correct − wrong) / total)`，WRONG = −1.0
- 最终准确率 = 对已测层级取均值

---

## 3. 完整工作流程

```
第一阶段——探针生成（一次性，已冻结）
  01_generate_probes.py + 09_researcher_probes.py
  → final_probe_set_v8.json（1,400 道题）

第二阶段——校准（一次性）
  02_run_calibration.py + 03_fit_calibration.py
  → calibration_fit.json

第三阶段——估算新模型（用户路径）
  scripts/ikp_estimate.py
  → 加载探针 → 查询模型（16 并发）→ 裁判评分 → 层级得分 → log10(P)

第四阶段——研究 / 论文路径
  run_all_models.py（188 个模型）→ generate_figures.py → latexmk
```

---

## 4. 核心发现

1. **对数线性缩放定律** — R²=0.917，跨越四个数量级
2. **MoE：总参数 > 活跃参数** — 知识存储容量取决于总权重数量
3. **思考模式：适度提升** — 对 T3–T5（需推断）帮助大于 T6–T7（纯粹回忆）
4. **幻觉指纹** — 错误答案集的 Jaccard 相似度可检测共享训练数据和模型谱系
5. **Densing 定律证伪** — 控制参数量后，知识能力随时间无显著增长
6. **研究者识别率 ∝ 引用数** — Spearman ρ = 0.575

---

## 5. 实际应用场景

| 场景 | 方法 |
|---|---|
| 估算闭源模型规模 | 对 API 运行 `ikp_estimate.py` |
| 检测端点静默换模型 | 每周定期运行；准确率下降 = 换了更小模型 |
| 测试本地/量化模型 | `--tiers T4,T5,T6,T7 --api-base localhost` |
| 衡量微调的知识损失 | 微调前后各跑一次，对比逐层分项 |
| 检测 RAG / 外部检索 | T7 得分异常高 = 疑似外挂检索 |
| 检测模型谱系 / 蒸馏 | 错误答案集的 Jaccard 相似度 |

---

## 6. 扩展方向

- **多语言 IKP** — 中文/日语/阿拉伯语探针（`08_chinese_probes.py` 已作为起点）
- **领域专属校准曲线** — 按领域分别拟合，检测专业化模型
- **时间性重校准** — 定期在新的开源模型组上重新拟合
- **整合到排行榜** — 为 HF Open LLM Leaderboard 增加知识广度维度
- **多模态探针** — 视觉知识层级，用于 VLM
- **对抗性探针** — 虚假记忆探针，衡量过度自信
- **持续端点监控** — 检测厂商 API 的静默模型替换

---

## 7. 快速参考

| 目标操作 | 命令（在 `ikp_study/` 根目录运行） |
|---|---|
| 估算一个模型 | `python scripts/ikp_estimate.py -m openai/gpt-4.1` |
| 快速估算 | `... --sample 200` |
| 本地模型只测困难层级 | `... --api-base http://localhost:8000/v1 --api-key EMPTY --tiers T4,T5,T6,T7` |
| 思考模式 | `... --thinking` |
| 导出结果为 JSON | `... -o out.json` |
| 查看校准曲线 | `... --show-calibration` |
| 浏览探针集 | `... --inspect-probes` |
| 上游脚本（不含 --tiers） | `python ikp/scripts/ikp_estimate.py -m MODEL` |
| 上游交互式 CLI | `cd ikp && python -m cli research --researcher "姓名"` |
| 批量评分所有模型 | `cd ikp && python scripts/run_all_models.py --skip-existing` |
| 重新生成所有图表 | `cd ikp && python paper/figures/generate_figures.py` |
