# IKP 配套网站

基于 React + Vite + TailwindCSS 的交互式网站，可视化校准曲线、逐层级准确率、指纹热力图、Densing 定律证伪等内容。

在线访问：<https://01.me/research/ikp>

## 技术栈

- **React 18** + **TypeScript** + **react-router-dom**
- **Vite 5** + **TailwindCSS 3** + **Recharts**
- 纯静态输出（`website/dist/`）；无需服务器运行时

## 开发

```bash
cd website && npm install
make website-dev     # 数据刷新 + vite 开发服务器 → http://localhost:5173
```

## 数据刷新

新模型加入 `data/results/` 后须重新运行：

```bash
make website         # 从仓库根目录运行
# 等价于：python3 website/scripts/prepare_data.py
```

## 生产构建与部署

```bash
make website-build   # 静态构建 → website/dist/
make website-preview # 预览 → http://localhost:4173
make website-deploy  # rsync 到 DEPLOY_HOST:DEPLOY_PATH
```

覆盖部署目标：

```bash
make website-deploy DEPLOY_HOST=user@host DEPLOY_PATH=/var/www/path/
```

nginx 配置（哈希路由无需 SPA 回退）：

```nginx
location /research/ikp/ {
    alias /var/www/01.me/research/ikp/;
}
```

GitHub Pages：

```bash
make website-build
cd website && \
  git --work-tree=dist add --all && \
  git --work-tree=dist commit -m "deploy" && \
  git push origin HEAD:gh-pages --force
```

## 部署前健全性检查

1. `make website-build` 退出码为 0
2. `website/public/data/calibration.json` 显示 `n=89`、`R²≈0.917`
3. 点击 `/calibration`、`/densing`、`/fingerprint`、`/models/<model>`、`/probes` 均无控制台错误
4. 右上角标题显示 `188 models · 1,400 probes · 27 vendors`
