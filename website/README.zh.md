# IKP 配套网站（中文说明）

> 本文件为 [`ikp/website/README.md`](../ikp/website/README.md) 的中文翻译。
> 所有网站源码位于 `ikp/website/` 子模块目录下。

在线访问：<https://01.me/research/ikp>

## 开发与构建

```bash
cd ikp/website && npm install
make website-dev     # 开发服务器 → http://localhost:5173
make website-build   # 静态构建 → ikp/website/dist/
make website-deploy  # rsync 到 DEPLOY_HOST:DEPLOY_PATH
```

（以上 `make` 命令从 `ikp/` 目录运行）

## 数据刷新

新模型加入 `ikp/data/results/` 后须重新运行：

```bash
cd ikp && make website
# 等价于：python3 website/scripts/prepare_data.py
```

## 部署前健全性检查

1. `make website-build` 退出码为 0
2. `ikp/website/public/data/calibration.json` 显示 `n=89`、`R²≈0.917`
3. 点击 `/calibration`、`/densing`、`/fingerprint`、`/models/<model>`、`/probes` 均无控制台错误
4. 右上角标题显示 `188 models · 1,400 probes · 27 vendors`
