# scripts/ 目录（ikp_study 扩展）

本目录包含对上游 `ikp/scripts/` 的扩展脚本。

## 三条执行路径

IKP 估算可以走三条互斥的路径，对应不同的“如何调用被测模型”：

| 路径 | 脚本 | 被测模型怎么访问 | 何时使用 |
|---|---|---|---|
| **HTTP API（vLLM / OpenRouter）** | `ikp_estimate.py` | 通过 OpenAI 兼容 HTTP 端点（任意 `--api-base`） | 评估本地 vLLM / llama.cpp / Ollama，或 OpenRouter 上的托管模型 |
| **Agent — Claude（`claude -p`）** | `ikp_estimate_claude_cli.py` | shell out 到本地 `claude` CLI（headless） | 评估 Claude Code 订阅下的 Claude 模型（Opus / Sonnet / Haiku），无需 Anthropic API Key |
| **Agent — Codex（`codex exec`）** | `ikp_estimate_codex_cli.py` | shell out 到本地 `codex` CLI（headless） | 评估 ChatGPT Codex 订阅下的 OpenAI 模型（gpt-5.5 等），无需 OpenAI API Key |

三条路径互不依赖：
- HTTP 路径需要一个起好的推理后端 + `OPENROUTER_API_KEY`（给 Gemini 裁判用）。
- Agent / Claude 路径只需要 `claude` CLI 登录；裁判默认 Haiku 4.5。
- Agent / Codex 路径只需要 `codex` CLI 登录；裁判默认 gpt-5.5 自身（自评有偏，文档里有说明）。

## 脚本一览

| 脚本 | 路径 | 用途 |
|---|---|---|
| `ikp_estimate.py` | HTTP API | 修改版估算脚本，新增 `--tiers` 过滤；数据路径自动指向 `ikp/` 子模块。详见 [`../TOOLKIT.zh.md`](../TOOLKIT.zh.md)。 |
| `ikp_estimate_claude_cli.py` | Agent / Claude | 通过 `claude -p` 子进程评估 Claude Code 模型；`--system-prompt` 覆盖默认提示词、`--tools ""` 禁用工具，每题一次独立会话。详见 [`../TOOLKIT_AGENT.zh.md`](../TOOLKIT_AGENT.zh.md)（变体 1）。 |
| `ikp_estimate_codex_cli.py` | Agent / Codex | 通过 `codex exec` 子进程评估 ChatGPT-backed 模型；`-c plugins={}` 关掉 superpowers 自动加载，每题一次独立会话。详见 [`../TOOLKIT_AGENT.zh.md`](../TOOLKIT_AGENT.zh.md)（变体 2）。 |

## 上游脚本（位于 `ikp/scripts/`）

| 脚本 | 用途 |
|---|---|
| `ikp/scripts/ikp_estimate.py` | 原版单模型估算器（不含 `--tiers`）。 |
| `ikp/scripts/run_all_models.py` | 批量评分 `configs/all_models.json` 中的所有模型。 |
| `ikp/scripts/run_evaluation.py` | 按名称评分单个模型。 |

上游完整脚本索引见 [`ikp/scripts/README.md`](../ikp/scripts/README.md)。

## 快速对照

```bash
# HTTP API 路径（vLLM 本地服务）
export OPENROUTER_API_KEY=sk-or-...
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model my-model --tiers T4,T5,T6,T7

# Agent / Claude 路径（claude -p 全 1400 题）
python scripts/ikp_estimate_claude_cli.py \
    --model claude-opus-4-7 \
    --judge-model claude-haiku-4-5 \
    --workers 8 \
    --output results/claude-opus-4-7-claude-cli.json

# Agent / Codex 路径（codex exec 全 1400 题）
python scripts/ikp_estimate_codex_cli.py \
    --model gpt-5.5 --effort low \
    --judge-model gpt-5.5 --judge-effort low \
    --workers 8 \
    --output results/gpt-5.5-codex.json
```
