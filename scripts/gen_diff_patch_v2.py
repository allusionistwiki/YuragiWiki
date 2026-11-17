"""Canonical generator for scripts/patches/build-diff-build.patch.mjs (v2).

Pars parent (59cf5d1) + patch == head (54b5b14) + processed-cache coverage
guard, then writes the patch module with JSON string literals (engine-decoded,
no template escaping involved).

Run:  python scripts/gen_diff_patch_v2.py
Then: node scripts/apply-quartz-patches.mjs   (idempotent; verifies esbuild parse)
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "scripts" / "patches" / "build-diff-build.patch.mjs"
BS, NL, BT, D, Q = chr(92), chr(10), chr(96), chr(36), chr(34)


def show(rev):
    return subprocess.run(
        ["git", "show", rev + ":quartz/build.ts"],
        capture_output=True, cwd=ROOT, encoding="utf-8", errors="replace").stdout.replace(BS + chr(13) + NL, NL)


parent, head = show("59cf5d1"), show("54b5b14")


def region(s, a, b):
    i = s.index(a)
    j = s.index(b, i)
    return s[i : j + len(b)]


# imports: 3-line header -> expanded header
imp_old = region(
    parent,
    "import { existsSync, mkdirSync, readFileSync, writeFileSync } from " + Q + "node:fs" + Q,
    "import { gunzipSync, gzipSync } from " + Q + "node:zlib" + Q)
imp_new = region(
    head,
    "import { existsSync, mkdirSync, readFileSync, writeFileSync, createReadStream, createWriteStream } from " + Q + "node:fs" + Q,
    "import rfdc from " + Q + "rfdc" + Q)
assert imp_old in parent and imp_new in head

# diffFlow: sync writeDiffState call -> awaited
flow_a = "  const prevManifest = process.env.QUARTZ_PREV_MANIFEST"
flow_b = "  await emitContent(ctx, filteredContent)" + NL + "  writeDiffState(ctx, filteredContent)"
flow_b_new = "  await emitContent(ctx, filteredContent)" + NL + "  await writeDiffState(ctx, filteredContent)"
flow_old = region(parent, flow_a, flow_b)
flow_new = region(head, flow_a, flow_b_new)
assert flow_old in parent and flow_new in head

# diffImpl: parent tail (CI comment .. EOF) -> guarded head tail
impl_a = "// CI 差分ビルド（QUARTZ_DIFF=1 のときだけ）: manifest の sha256 と比べ、"
assert impl_a in parent and impl_a in head
impl_old = parent[parent.index(impl_a):]

cache_guard = NL.join([
    "",
    "  const cachePath = process.env.QUARTZ_PROCESSED_CACHE ?? " + Q + ".quartz-cache/processed.jsonl.gz" + Q,
    "  if (!existsSync(cachePath)) {",
    "    throw new Error(" + BT + "diff build: processed cache missing at " + D + "{cachePath} — full build required" + BT + ")",
    "  }",
    "  // processed スナップショットは JSONL（1 ページ 1 行 gzip）なのでストリームで",
    "  // 1 行ずつ読む（JSON.parse 単発は V8 の 512MB 文字列/バッファ上限に当たる）。",
    "  const cacheLines: string[] = []",
    "  {",
    "    const rl = createInterface({",
    "      input: createReadStream(cachePath).pipe(createGunzip()),",
    "      crlfDelay: Infinity,",
    "    })",
    "    for await (const line of rl) {",
    '      if (line.trim() === "") continue',
    "      cacheLines.push(line)",
    "    }",
    "  }",
    "  // キャッシュが未変更全数をカバーしない（古い・部分的）なら差分ビルドの",
    "  // 利点がないので full parse へ完全退避する（restored+parsed >= pages を保証）。",
    "  if (cacheLines.length < filePaths.length - changedPaths.length) {",
    "    console.log(",
    "      styleText(",
    "        " + Q + "yellow" + Q + ",",
    "        " + BT + "diff: processed cache covers " + D + "{cacheLines.length} < " + D + "{filePaths.length - changedPaths.length} unchanged pages — falling back to full parse" + BT + ",",
    "      ),",
    "    )",
    "    const parsedAll = await parseMarkdown(ctx, filePaths)",
    "    for (const fp of filePaths) {",
    "      DIFF_PAGES[relOf(ctx, fp)] = createHash(" + Q + "sha256" + Q + ").update(readFileSync(fp)).digest(" + Q + "hex" + Q + ")",
    "    }",
    "    return parsedAll",
    "  }",
    "  const cached: { pages?: any[] } = { pages: [] }",
    "  for (const line of cacheLines) {",
    "    cached.pages!.push(JSON.parse(line))",
    "  }",
    "  const parsedNew = await parseMarkdown(ctx, changedPaths)",
    "",
])
head_cache_start = head.index("  const parsedNew = await parseMarkdown(ctx, changedPaths)")
head_cache_end = head.index("  const DATE_KEYS = [" + Q + "date" + Q)
expected = head[:head_cache_start] + cache_guard[1:] + head[head_cache_end:]
impl_base_new = head[head.index(impl_a):]            # 54b5b14 tail (no guard)
impl_guard_new = expected[expected.index(impl_a):]   # guarded tail
# canonical order: imports -> flow -> guard (the committed 54b5b14 state applies
# cleanly; the 59cf5d1 pre-diff state is covered by the explicit rebuild recipe
# in the header comment below).
sim = parent.replace(imp_old, imp_new).replace(flow_old, flow_new).replace(impl_old, impl_guard_new)
ok = sim == expected
print("VERIFY parent+patch == 54b5b14+guard:", ok)
if not ok:
    a, b = sim, expected
    lo = 0
    while lo < min(len(a), len(b)) and a[lo] == b[lo]:
        lo += 1
    print("lens:", len(a), len(b), "first diverge at", lo)
    print("SIM:", repr(a[max(0, lo - 60): lo + 40]))
    print("EXP:", repr(b[max(0, lo - 60): lo + 40]))
    raise SystemExit(1)

header_lines = [
    "/**",
    " * Quartz 差分デプロイ・エンジン patch（冪等）。build checkout (59cf5d1) へ適用すると",
    " * 54b5b14 + processed キャッシュカバレッジ guard になる。",
    " *   imports  : 差分ビルドが必要する node:fs 拡張・zlib stream・readline・rfdc",
    " *   diffFlow : 差分状態書き込みを await する",
    " *   diffImpl : 差分 parse 本体（manifest 照合・変更分だけ LLM・未変更は",
    " *              processed.jsonl.gz から復元）。キャッシュが未変更全数をカバー",
    " *              しない場合は full parse へ完全退避する guard を含む。",
    " * リテラルは JSON 文字列（\\u エスケープ）。JS エンジンが正確に復元する。",
    " */",
    "export const PATCH = {",
    "  imports: {",
    '    file: "quartz/build.ts",',
    '    description: "diff build engine imports",',
    "    oldString: __IMP_OLD__,",
    "    newString: __IMP_NEW__,",
    "  },",
    "  diffFlow: {",
    '    file: "quartz/build.ts",',
    '    description: "await writeDiffState in buildQuartz",',
    "    oldString: __FLOW_OLD__,",
    "    newString: __FLOW_NEW__,",
    "  },",
    "  diffImplGuard: {",
    '    file: "quartz/build.ts",',
    '    description: "processed-cache coverage guard (full-parse fallback)",',
    "    oldString: __IMPL_GUARD_OLD__,",
    "    newString: __IMPL_GUARD_NEW__,",
    "  },",
    "}",
    "",
    '/* 59cf5d1 からの再構築レシピ（その状態は git 履歴にしか存在しない）:',
    '   node scripts/apply-quartz-patches.mjs は 54b5b14 系の状態（コミット済み）',
    '   に対して imports・flow・guard を適用する。59cf5d1 へ戻す必要が出たら',
    '   git checkout 59cf5d1 -- quartz/build.ts 後、このファイルの diffImplBase',
    '   相当（54b5b14 差分）を先に適用し、通常の apply を続けること。 */',
    "",
    'export function patchText(src, path = "quartz/build.ts") {',
    "  const parts = Object.keys(PATCH)",
    "  const get = (p, k) => PATCH[p][k]",
    '  const has = (p) => src.includes(get(p, "newString"))',
    "  if (parts.every(has)) return src // fully applied: idempotent no-op",
    "  for (const p of parts) {",
    '    const n = get(p, "newString")',
    '    const o = get(p, "oldString")',
    "    if (src.includes(n)) continue",
    "    if (src.includes(o)) {",
    "      src = src.replace(o, n)",
    "      continue",
    "    }",
    "    throw new Error(",
    "      path + ': patch part \\'' + p + '\\' matches neither old nor new block',",
    "    )",
    "  }",
    "  return src",
    "}",
]
out = NL.join(header_lines)
for k, v in {
    "__IMP_OLD__": imp_old, "__IMP_NEW__": imp_new,
    "__FLOW_OLD__": flow_old, "__FLOW_NEW__": flow_new,
    "__IMPL_BASE_OLD__": impl_old, "__IMPL_BASE_NEW__": impl_base_new,
    "__IMPL_GUARD_OLD__": impl_base_new, "__IMPL_GUARD_NEW__": impl_guard_new,
}.items():
    out = out.replace(k, json.dumps(v))
P.write_text(out, encoding="utf-8", newline=NL)
print("patch file written (JSON literals)")
