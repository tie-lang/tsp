# -*- coding: utf-8 -*-
# lsp_mem.py —— tsp 内存峰值/稳态对比（p.9.16.5 验收度量）
# ============================================================
# 用途：同一负载下量化「前端 AST 用后释放（p.9.16.2）+ 去冗余（p.9.16.3）」的内存收益。
# 负载：打开 docs 个合成文档（每个 ~1200 行 tie 源码）→ 对每个文档做 rounds 次
#       didChange（改一处标识符，触发整条前端管线重跑）。
# 采样：每步读进程 WorkingSetSize / PeakWorkingSetSize（psapi，无第三方依赖）。
#
# 用法：
#   python lsp_mem.py <tsp.exe> [docs] [rounds]
#   TSP_LAZY=0 python lsp_mem.py ...      # 关闭「用后释放」做 A/B 对照
#
# 为什么是 .py 而不是 .tsh.tie：这是 LSP 探针族（lsp_smoke*.py）的同类件，
# 需在测试进程内采样被测进程的内存（tsh 脚本没有等价的内存采样原语）。
import ctypes, ctypes.wintypes as wt, json, os, subprocess, sys, threading, time


class PMC(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


def mem_of(pid):
    h = ctypes.windll.kernel32.OpenProcess(0x0410, False, pid)  # QUERY_INFORMATION|VM_READ
    if not h:
        return (0, 0, 0)
    pmc = PMC()
    pmc.cb = ctypes.sizeof(PMC)
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb)
    ctypes.windll.kernel32.CloseHandle(h)
    if not ok:
        return (0, 0, 0)
    return (pmc.WorkingSetSize // 1024, pmc.PeakWorkingSetSize // 1024, pmc.PagefileUsage // 1024)


def frame(msg):
    b = json.dumps(msg, ensure_ascii=False).encode('utf-8')
    return b'Content-Length: %d\r\n\r\n' % len(b) + b


def drain(f, sink):
    while True:
        c = f.read(4096)
        if not c:
            return
        sink.append(c)


def gen_src(tag, nfuncs=60, body=16):
    """生成一段合成 tie 源码（~1200 行）。tag 用于让不同文档内容不同。"""
    out = ["type tie<logic>", ""]
    for i in range(nfuncs):
        out.append("pub func f_%s_%d(a: i64, b: i64) -> i64 {" % (tag, i))
        out.append("    var acc: i64 = a + b")
        for j in range(body):
            out.append("    var v%d: i64 = acc * %d + %d" % (j, j + 1, i))
            out.append("    acc = acc + v%d" % j)
        out.append("    return acc")
        out.append("}")
        out.append("")
    out.append("func main() -> i64 {")
    out.append("    return f_%s_0(1, 2)" % tag)
    out.append("}")
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        print("usage: python lsp_mem.py <tsp.exe> [docs] [rounds]")
        return 2
    tsp = sys.argv[1]
    ndocs = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 12

    p = subprocess.Popen([tsp], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sink = []
    errs = []
    threading.Thread(target=drain, args=(p.stdout, sink), daemon=True).start()
    threading.Thread(target=drain, args=(p.stderr, errs), daemon=True).start()

    def send(msg):
        if p.poll() is not None:
            raise SystemExit("tsp 已退出 rc=%s OUT=%r ERR=%r" % (p.poll(), b''.join(sink)[-300:], b''.join(errs)[-300:]))
        p.stdin.write(frame(msg))
        p.stdin.flush()

    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"processId": None, "rootUri": "file:///REDACTED_LOCAL_PATH", "capabilities": {}}})
    send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
    time.sleep(0.3)
    base_ws, base_peak, base_cm = mem_of(p.pid)

    cur = []
    for i in range(ndocs):
        uri = "file:///REDACTED_LOCAL_PATH/_z/mem/d%d.tie" % i
        txt = gen_src("d%d" % i)
        cur.append(txt)
        send({"jsonrpc": "2.0", "method": "textDocument/didOpen",
              "params": {"textDocument": {"uri": uri, "languageId": "tie", "version": 1, "text": txt}}})
    time.sleep(0.5)
    after_open_ws, after_open_peak, after_open_cm = mem_of(p.pid)

    # 每一轮都制造「真文本变化」（改首处 return 行）⇒ 每轮都实跑整条前端管线，
    # 不做「文本未变命中缓存」的短路——否则测不出 AST 物化的开销。
    for r in range(rounds):
        d = r % ndocs
        uri = "file:///REDACTED_LOCAL_PATH/_z/mem/d%d.tie" % d
        cur[d] = cur[d].replace("return acc", "return acc + %d" % (r + 1), 1)
        send({"jsonrpc": "2.0", "method": "textDocument/didChange",
              "params": {"textDocument": {"uri": uri, "version": r + 2},
                         "contentChanges": [{"text": cur[d]}]}})
        time.sleep(0.12)

    steady_ws, steady_peak, steady_cm = mem_of(p.pid)
    send({"jsonrpc": "2.0", "id": 9, "method": "shutdown", "params": None})
    send({"jsonrpc": "2.0", "method": "exit", "params": None})
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()

    print("tsp            = %s" % tsp)
    print("TSP_LAZY       = %s" % os.environ.get("TSP_LAZY", "(default=1)"))
    print("docs=%d rounds=%d" % (ndocs, rounds))
    print("base   ws=%6d KB  peak=%6d KB  commit=%6d KB" % (base_ws, base_peak, base_cm))
    print("open   ws=%6d KB  peak=%6d KB  commit=%6d KB" % (after_open_ws, after_open_peak, after_open_cm))
    print("steady ws=%6d KB  peak=%6d KB  commit=%6d KB" % (steady_ws, steady_peak, steady_cm))
    print("RESULT ws=%d peak=%d commit=%d open_ws=%d" % (steady_ws, steady_peak, steady_cm, after_open_ws))
    return 0


if __name__ == '__main__':
    sys.exit(main())
