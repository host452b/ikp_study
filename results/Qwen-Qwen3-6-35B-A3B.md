        # Benchmark Results: Qwen/Qwen3.6-35B-A3B

        **Date:** 2026-04-30
        **Notes:** MoE 35B total / 3B active, BF16
        **Environment:** vLLM 0.20.0, 1× NVIDIA GPU (183 GB VRAM)
        **Judge:** same local model (self-judge)
        **Probes:** IKP probe set v8, 1,400 probes × 7 tiers (T1–T7)

        ## How to Run

        ```bash
        # 1. Start vLLM server
        vllm serve Qwen/Qwen3.6-35B-A3B \
            --port 8000 --tensor-parallel-size 1 \
            --max-model-len 4096 --gpu-memory-utilization 0.9

        # 2. Run benchmark
        python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model Qwen/Qwen3.6-35B-A3B \
    --judge-api-base http://localhost:8000/v1 \
    --judge-model Qwen/Qwen3.6-35B-A3B \
    --workers 8
        ```

        > Note: Qwen3 series models output internal thinking by default.
        > This script now auto-disables thinking via `chat_template_kwargs={"enable_thinking": false}`
        > for any model whose name contains "qwen3" (case-insensitive).

        ## Results

        | Metric | Value |
        |---|---|
        | Penalized accuracy | 36.4% |
        | Raw accuracy | 49.3% |
        | **Estimated parameters** | **38B** |
        | Effective tier | T3 |

        | Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 99% | 199 | 1 | 0 | 200 |
| T2 | 96% | 196 | 4 | 0 | 200 |
| T3 | 60% | 159 | 39 | 2 | 200 |
| T4 | 0% | 88 | 100 | 12 | 200 |
| T5 | 0% | 32 | 108 | 60 | 200 |
| T6 | 0% | 10 | 116 | 74 | 200 |
| T7 | 0% | 6 | 96 | 98 | 200 |

        ## Issues and Fixes

        ### Qwen3 default thinking mode
        **Problem:** Qwen3.6 (and Qwen3 series) models output their internal reasoning
        directly into the `content` field by default. The IKP judge model would receive
        a multi-paragraph thinking trace and classify every answer as WRONG.

        **Fix:** Added `is_qwen3_model()` detection in `scripts/ikp_estimate.py`.
        When the model name contains "qwen3" and `--thinking` is not set, the script
        injects `"chat_template_kwargs": {"enable_thinking": false}` into both the
        query payload and the judge payload. This keeps responses clean and one-line.

        ### Self-judge bias note
        Using the same model as both subject and judge introduces circular bias.
        Results are directionally valid but an independent judge would be more accurate.
