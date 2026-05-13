# IKP 估算工具包 —— Agent 路径（`claude -p`）

> **两条路径,两份工具说明。** 本文档介绍 **Agent 路径**——
> `scripts/ikp_estimate_claude_cli.py`,通过 shell 调用本地 `claude` CLI
> 的 headless 模式(每道探针一次 `claude -p`)。
>
> 若要评估 OpenAI 兼容的 HTTP 端点(vLLM、llama.cpp、Ollama、OpenRouter),
> 请走 HTTP API 路径:[`TOOLKIT.zh.md`](TOOLKIT.zh.md)。

## 何时使用本路径

- 你想在 IKP 上评估 Claude Code 模型(Opus / Sonnet / Haiku)。
- 你已经 `claude` CLI 登录但没有 Anthropic API Key。
- 你不想(或无法)起一个 HTTP 推理服务。

被测对象就是 Claude Code 订阅本身。每道探针起一个独立的 `claude -p` 子进程,
探针之间不共享上下文——这等价于 vLLM 处理无状态 HTTP 请求的方式。

## 一键运行

```bash
python scripts/ikp_estimate_claude_cli.py \
    --model claude-opus-4-7 \
    --judge-model claude-haiku-4-5 \
    --workers 8 \
    --output results/claude-opus-4-7-claude-cli.json
```

如果在公司代理后面:

```bash
HTTP_PROXY=http://proxy.example.com:3128 \
HTTPS_PROXY=http://proxy.example.com:3128 \
python scripts/ikp_estimate_claude_cli.py --model claude-opus-4-7
```

代理环境变量会自动转给每个 `claude -p` 子进程。

## CLI 参考

### 模型

| 参数 | 默认值 | 用途 |
|---|---|---|
| `--model, -m MODEL` | `claude-opus-4-7` | 被测模型名(任何 `claude --model` 接受的别名)。 |
| `--judge-model MODEL` | `claude-haiku-4-5` | 裁判模型(同样走 `claude -p`)。Haiku 独立于 Opus,可避免自评偏差。 |

### 评测

| 参数 | 默认值 | 用途 |
|---|---|---|
| `--sample, -n N` | 全部 1400 | 分层随机抽样:每层 `N/7` 道。 |
| `--tiers TIERS` | 全部 7 层 | 逗号分隔层级,如 `T4,T5,T6,T7`。 |
| `--workers, -w N` | 8 | 并行子进程数。Power Users 订阅下 8 比较稳;4–16 都合理。 |
| `--sequential, -s` | 关闭 | 强制串行(`workers=1`)。 |
| `--output, -o FILE` | — | 把逐探针结果 + 层级统计写入 JSON。 |
| `--progress-file FILE` | — | 每完成一道追加一行 JSON,可 `tail -f` 实时看进度。 |

### 检查

| 参数 | 用途 |
|---|---|
| `--inspect` | 评分后打印每道题的模型回答、标准答案和裁定。 |
| `--inspect-probes` | 按层级打印探针并退出(不调用 CLI)。 |

## 工作原理

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

- `--system-prompt` **替换** Claude Code 默认 system prompt,改用 IKP 风格的事实提问 prompt,
  和 HTTP 路径发送的 `SYSTEM_MSG` 完全一致。
- `--tools ""` + `--disable-slash-commands` 关闭所有工具/skill/插件,
  保证模型只用自身参数化知识回答。
- `--no-session-persistence` 不把会话状态写盘。
- `--output-format json` 返回一个 JSON 对象,脚本从 `result` 字段读模型回答。

裁判调用同一套外壳,换不同的 system prompt(`JUDGE_SYSTEM`)和包含 IKP 评分规则的 user message。

## 注意事项

- **子进程开销实打实存在。** 每次 `claude -p` 启动 Node + Claude Code 会有 ~1–2 秒的固定开销,
  叠加在 API 调用时间之上。8 workers 下整机大约 0.6 题/秒(1400 题完整跑约 35–40 分钟)。
- **校准曲线仍用开源权重模型锚定。** 89 个开源模型校准出的
  `log10(params_B) = 6.79 · acc − 0.899` 映射照用。
  对闭源 Claude 模型来说,"估计参数量"读作*"想达到这个准确率,一个开源模型需要多大"*更准确,
  而不是 Claude 的真实参数量。
- **没有 `--thinking` 开关。** 推理力度由 model alias 和 Claude Code 默认决定;
  如果要对比 thinking 模式,可改 `run_claude_cli` 加入 `--effort`,
  或者分两次运行不同配置。
