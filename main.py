name: Deploy Pygame to Web

on:
  push:
    branches: [ main ]  # 如果你的主分支叫 master，请改为 master

# 🔑 核心修复：显式声明写入权限，解决 403 错误
permissions:
  contents: write

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Pygbag
        run: |
          python -m pip install --upgrade pip
          pip install pygbag

      - name: Build Web Version
        run: |
          # 编译 main.py 为 WebAssembly
          # --build 参数会生成 build/web 目录
          pygbag --build $GITHUB_WORKSPACE/main.py

      - name: Deploy to GitHub Pages
        uses: JamesIves/github-pages-deploy-action@v4
        with:
          folder: build/web     # Pygbag 生成的网页文件所在位置
          branch: gh-pages      # 部署到的目标分支
          silent: false         # 打印详细日志，方便排查
