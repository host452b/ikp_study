# IKP 估算工具包 —— Agent 路径

> **两条路径,两份工具说明。** 本文档介绍 **Agent 路径**——通过 headless coding-agent CLI
> 跑(每道探针一个子进程),不走 HTTP API。支持两种 CLI,各有一个脚本:
>
> | CLI | 脚本 | 已登录的模型 |
> |---|---|---|
> | `claude -p`(Anthropic Claude Code) | `scripts/ikp_estimate_claude_cli.py` | claude-opus-4-7 / sonnet / haiku |
> | `codex exec`(OpenAI Codex CLI) | `scripts/ikp_estimate_codex_cli.py` | gpt-5.5(以及其他 ChatGPT 后端的模型) |
>
> 若要评估 OpenAI 兼容的 HTTP 端点(vLLM、llama.cpp、Ollama、OpenRouter),
> 请走 HTTP API 路径([`TOOLKIT.zh.md`](TOOLKIT.zh.md))。

## 何时用本路径

- 想评估某个 coding-agent 订阅(Claude Code 或 ChatGPT Codex)背后的模型,但又不想去申请该厂的 API Key。
- 不想(或无法)起一个 HTTP 推理服务。
- 每道探针都起一个新的 CLI 子进程,探针之间不共享上下文——和 vLLM 处理无状态请求等价。

---

## 变体 1 — Claude Code(`claude -p`)

### 一键运行

```bash
python scripts/ikp_estimate_claude_cli.py \
    --model claude-opus-4-7 \
    --judge-model claude-haiku-4-5 \
    --workers 8 \
    --output results/claude-opus-4-7-claude-cli.json
```

代理环境变量(`HTTP_PROXY` / `HTTPS_PROXY`)会被自动转给每个 `claude -p` 子进程。

### CLI 参考

| 参数 | 默认值 | 用途 |
|---|---|---|
| `--model, -m MODEL` | `claude-opus-4-7` | 被测模型(任何 `claude --model` 接受的别名)。 |
| `--judge-model MODEL` | `claude-haiku-4-5` | 裁判模型——Haiku 独立于 Opus,避免自评偏差。 |
| `--sample, -n N` | 全部 1400 | 分层随机抽样:每层 `N/7` 道。 |
| `--tiers TIERS` | 全部 7 层 | 逗号分隔,如 `T4,T5,T6,T7`。 |
| `--workers, -w N` | 8 | 并行子进程数。Power Users 订阅下 4–16 都行。 |
| `--sequential, -s` | 关闭 | 强制 `workers=1`。 |
| `--output, -o FILE` | — | 把逐探针结果 + 层级统计写到 JSON。 |
| `--progress-file FILE` | — | 每完成一道追加一行 JSON。 |
| `--inspect` | 关闭 | 评分后打印每道题的详情。 |
| `--inspect-probes` | 关闭 | 按层级打印探针并退出。 |

### 工作原理

每道探针对应一次:

```bash
claude -p \
    --model claude-opus-4-7 \
    --no-session-persistence \
    --disable-slash-commands \
    --tools "" \
    --system-prompt "Answer factual questions directly and concisely. If you don't know, say 'I don't know'." \
    --output-format json \
    "<探针题>"
```

- `--system-prompt` **替换** Claude Code 默认 system prompt,改用 IKP 风格的事实提问 prompt。
- `--tools ""` + `--disable-slash-commands` 关闭所有工具/skill/插件,保证模型只用参数化知识回答。
- `--no-session-persistence` 不把会话状态写盘。
- `--output-format json` 返回 JSON 对象,脚本从 `result` 字段读模型回答。

### 注意事项(Claude 变体)

- 子进程启动开销 ~1–2 s。8 workers 下 ~0.6 题/秒(1400 题约 35–40 分钟)。
- 没有 `--thinking` 开关。如果要试 thinking 模式,需要改 `run_claude_cli`。

---

## 变体 2 — ChatGPT Codex(`codex exec`)

### 一键运行

```bash
python scripts/ikp_estimate_codex_cli.py \
    --model gpt-5.5 --effort low \
    --judge-model gpt-5.5 --judge-effort low \
    --workers 8 \
    --output results/gpt-5.5-codex.json
```

代理环境变量会自动转给每个 `codex exec` 子进程。Codex 通过你的 ChatGPT 账号登录(`codex login status`)。

### CLI 参考

| 参数 | 默认值 | 用途 |
|---|---|---|
| `--model, -m MODEL` | `gpt-5.5` | 被测模型。 |
| `--effort LEVEL` | `xhigh` | `model_reasoning_effort`。**`minimal` 在 gpt-5.5 上是坏的(返回空)**;`low` 是可用的最低档;`xhigh` 是"最强版"但单题 wall-clock 约 5×。 |
| `--judge-model MODEL` | `gpt-5.5` | 裁判模型。 |
| `--judge-effort LEVEL` | `low` | 裁判 reasoning effort。`low` 快又稳。 |
| `--sample, -n N` | 全部 1400 | 分层抽样。 |
| `--tiers TIERS` | 全部 7 层 | 层级过滤。 |
| `--workers, -w N` | 4 | 默认比 Claude 变体小——codex 每次调用慢约 3×。8 也行,但持续并发会被限速。 |
| `--sequential, -s` | 关闭 | 强制串行。 |
| `--output, -o FILE` | — | 全量结果 JSON。 |
| `--progress-file FILE` | — | 实时 JSONL 流。 |

### 工作原理

每道探针对应一次:

```bash
codex exec \
    --skip-git-repo-check --ephemeral \
    --ignore-user-config --ignore-rules \
    -C /tmp -s read-only --color never \
    -o <tempfile> \
    -c plugins={} \
    -c service_tier="fast" \
    -m gpt-5.5 -c model_reasoning_effort="low" \
    "<IKP system prompt>\n\nQuestion: <探针题>"
```

- IKP 的 system message **被前置到 user prompt** 里,因为 `codex exec` 没有 `--system-prompt` 标志。
- `-c plugins={}` **关键**:不加的话,codex 每轮回答前会 shell 出来读自带的 `superpowers` 技能(`sed -n '1,200p' ~/.codex/superpowers/skills/.../SKILL.md`),严重污染基准,经常导致最终回答里夹带 thinking trace(如 `"W גSomething? Wait final..."`)。
- `-c service_tier="fast"` 在烟雾测试里加速 ~30%。
- `--ignore-user-config` + `-C /tmp` + `--ephemeral` 一起排除 `~/.codex/config.toml`、本地 `AGENTS.md` 和持久化会话。
- `-o <tempfile>` 干净地拿到最后一条 agent message——stdout 的 `--json` 事件流里掺杂 thinking 噪声。

### 注意事项(Codex 变体)

- **`minimal` effort 是坏的**:gpt-5.5 在该档下返回空字符串。脚本默认 `xhigh` 是按"最强版"意图配置的,但实际跑全量更适合 `--effort low`:`xhigh` 单题约 100 s × 8 workers → 1400 题约 5 小时;`low` 单题约 28 s → 约 2.5 小时。
- **自评偏差**——`--model` 和 `--judge-model` 用同一个模型会让 CORRECT 偏高。要更公允可换更小的 OpenAI 模型当裁判(如未来的 `gpt-5.5-mini`),或干脆用 Claude 变体当裁判。
- **限速**——8 workers 持续并发时偶尔掉到 ~0.13 题/秒,通常自动恢复。如果限速持续,降到 4–6 workers。
- 校准曲线沿用 89 个开源模型的开源拟合,闭源模型的"估计参数量"按"开源模型要多大才能达到这准确率"读。
