/** Quartz CI 差分ビルドのエンジン patch を適用する（冪等・CI/ローカル両対応）。
 *
 *   node scripts/apply-quartz-patches.mjs
 *
 * 各 patch モジュールは scripts/patches/*.patch.mjs に patchText(src) を export する。
 * 適用済み（newString を含む）なら no-op。適用前に構文チェックを通す
 * （esbuild transform で parse できること = 壊れた patch を commit しない）。
 */
import { readFileSync, writeFileSync, readdirSync } from "node:fs"
import path from "node:path"
import { pathToFileURL } from "node:url"
import { transformSync } from "esbuild"

import { fileURLToPath } from "node:url"
const ROOT = process.env.QUARTZ_PATCH_ROOT
  ? path.resolve(process.env.QUARTZ_PATCH_ROOT)
  : path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")
const TARGETS = [
  ["build-diff-build.patch.mjs", "quartz/build.ts"],
  ["links-internalize-site-urls.patch.mjs", "quartz/plugins/transformers/links.ts"],
]

let changed = 0
for (const [patchFile, target] of TARGETS) {
  const mod = await import(pathToFileURL(path.join(ROOT, "scripts", "patches", patchFile)).href)
  const targetPath = path.join(ROOT, target)
  const src = readFileSync(targetPath, "utf8")
  const out = mod.patchText(src, target)
  if (out !== src) {
    transformSync(out, { loader: "ts", tsconfigRaw: "{}" })
    writeFileSync(targetPath, out)
    console.log(`patched ${target} via ${patchFile}`)
    changed++
  } else {
    console.log(`already patched: ${target} via ${patchFile}`)
  }
}
console.log(`APPLY-QUARTZ-PATCHES done changed=${changed}`)
