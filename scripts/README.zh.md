# scripts/ 目录（ikp_study 扩展）

本目录包含对上游 `ikp/scripts/` 的扩展脚本。

## 本目录的脚本

| 脚本 | 用途 |
|---|---|
| `ikp_estimate.py` | 修改版估算脚本，新增 `--tiers` 层级过滤；路径自动指向 `ikp/` 子模块。详见 `../TOOLKIT.zh.md`。 |

## 上游脚本（位于 `ikp/scripts/`）

| 脚本 | 用途 |
|---|---|
| `ikp/scripts/ikp_estimate.py` | 原版单模型估算器（不含 `--tiers`）。 |
| `ikp/scripts/run_all_models.py` | 批量评分 `configs/all_models.json` 中的所有模型。 |
| `ikp/scripts/run_evaluation.py` | 按名称评分单个模型。 |

上游完整脚本索引见 [`ikp/scripts/README.md`](../ikp/scripts/README.md)。

## 使用说明

从 `ikp_study/` 根目录运行本目录的脚本：

```bash
# 使用本目录的修改版（支持 --tiers）
python scripts/ikp_estimate.py --model openai/gpt-4.1 --tiers T4,T5,T6,T7

# 使用上游原版
python ikp/scripts/ikp_estimate.py --model openai/gpt-4.1
```
