# tsp

**tie 语言服务器** / *Language server for the tie language*

tsp 是 tie 生态的 LSP（Language Server Protocol）实现：语义分析、补全、导航、重构、
签名文档与格式化，作为编辑器扩展（如 [tie-lang/vscode-tie](https://github.com/tie-lang/vscode-tie)）
的诊断后端，经 `tie --lsp` 启动。

*EN: tsp is the LSP implementation for the tie ecosystem: semantic analysis,
completion, navigation, refactoring, signature documentation and formatting.
It backs editor extensions (e.g. [tie-lang/vscode-tie](https://github.com/tie-lang/vscode-tie))
as the diagnostics engine, launched via `tie --lsp`.*

## 构建 / Build

tsp 由 tiec 编译（依赖 [tie-lang/tiec](https://github.com/tie-lang/tiec)）：

```bash
tiec server.tie -o tsp.exe
```

## 内容 / Contents

- `server.tie` 服务主入口；`protocol.tie` LSP 协议层
- `analyze` / `completion` / `nav` / `refactor` / `sigdoc` / `format` / `tokens` 语义能力模块
- `lsp_smoke*.py` 冒烟脚本与 `probe_*.tie` 探针（随源码仓分发）

## License

本仓库按 **Tie Public License v2.0（TPL 2.0）** 授权发布（全文见 [LICENSE](LICENSE)）：
你可自由使用、修改并分发本软件源码，包括用于商业产品，仅需保留版权声明并附本许可证。

EN: This repository is released under the **Tie Public License v2.0 (TPL 2.0)**
(full text in [LICENSE](LICENSE)): you may freely use, modify, and redistribute
the source code, including in commercial products, provided you retain the
copyright notice and a copy of the license.
