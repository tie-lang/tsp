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
tiec src/server.tie -o target/tsp.exe
```

## 内容 / Contents

- `src/server.tie` 服务主入口；`protocol.tie` LSP 协议层
- `analyze` / `completion` / `nav` / `refactor` / `sigdoc` / `format` / `tokens` 语义能力模块
- `role.tie` 文件角色（`type tie<...>`）识别：角色表与 tiec 的 `role_registry_init_default` 对齐
- `lsp_smoke*.py` 冒烟脚本与 `probe_*.tie` 探针（随源码仓分发）

## 文件角色 / File roles

tsp 认得 tie 的全部基础角色（`logic` `tsc` `class` `type` `lib` `ir` `test` `bench`
`data` `ui` `db` `port` `zd` `tsh` `tieir`）与修饰角色（`unsafe` `owned` `embedded`）。
角色语义本身由 tiec 判定，tsp 不重复实现：`type tie<lib>` 文件的「不允许定义 main」、
可承载模块命名空间等规则都经被调 tiec 生效，tsp 负责把结果映射成 LSP 诊断、
符号与着色。

被调 tiec 由环境变量 `TSP_TIEC` 指定；未设置时按 CWD 探测常见布局，且**合并后单仓**
（`tie` 仓的 `build/tiec.exe`）优先于合并前旧布局（`tiec` 仓的 `compiler/tiec.exe`）。
旧版 tiec 的角色表可能落后于当前语言（曾出现「不认识角色 `lib`」）；此时 tsp 会在
编译器错误之后追加一条警告，提示把 `TSP_TIEC` 指向当前编译器。

*EN: tsp knows every base role (`logic` `tsc` `class` `type` `lib` `ir` `test` `bench`
`data` `ui` `db` `port` `zd` `tsh` `tieir`) and modifier role (`unsafe` `owned` `embedded`)
of the tie language. Role semantics are enforced by the tiec it spawns; tsp maps the
results to diagnostics, symbols and highlighting. The compiler is selected by
`TSP_TIEC`; when unset, tsp probes common layouts and prefers the merged single-repo
build (`tie/build/tiec.exe`) over the pre-merge layout (`tiec/compiler/tiec.exe`).
If the spawned tiec predates a role, tsp appends a warning pointing at `TSP_TIEC`.*

## License

本仓库按 **Tie Public License v2.0（TPL 2.0）** 授权发布（全文见 [LICENSE](LICENSE)）：
你可自由使用、修改并分发本软件源码，包括用于商业产品，仅需保留版权声明并附本许可证。

EN: This repository is released under the **Tie Public License v2.0 (TPL 2.0)**
(full text in [LICENSE](LICENSE)): you may freely use, modify, and redistribute
the source code, including in commercial products, provided you retain the
copyright notice and a copy of the license.
