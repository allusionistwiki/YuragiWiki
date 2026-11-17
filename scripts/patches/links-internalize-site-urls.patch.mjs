/** 外部绝对 URL の内部化: site URL（AllusionistWiki2 配下）を指すリンクを
 *  Quartz 内部リンク（allSlugs 解決対象）として扱う patch。
 *  - `.../AllusionistWiki2/Lx/<section>/index.md` 形（層索引導線の恒久 URL）を
 *    markdown link transformer 通過後も内部 transform される形へ書き換える。
 *  - 相対 `../<section>/` 解決の root bare 404 問題を、内部 slug 解決へ
 *    寄せることで消す（層 top 導線は絶対 URL のまま運用可能になる）。
 */
const OLD = `                const isInternal = !(isAbsoluteUrl(dest) || dest.startsWith("#"))
                if (isInternal) {`
const NEW = `                // 内部化: この site (AllusionistWiki2) 配下の絶対 URL を
                // vault ルート相対 slug へ書き換えて内部解決させる（層導線規約）。
                const internalized = dest.replace(
                  /^https?:\\/\\/allusionistwiki\\.github\\.io\\/AllusionistWiki2\\/(.+)$/,
                  (_m, p1) => p1,
                )
                if (internalized !== dest) {
                  node.properties.href = internalized
                  dest = internalized
                }
                const isInternal = !(isAbsoluteUrl(dest) || dest.startsWith("#"))
                if (isInternal) {`

export function patchText(src) {
  if (src.includes("内部化: この site (AllusionistWiki2) 配下の絶対 URL を")) {
    return src
  }
  if (!src.includes(OLD)) {
    throw new Error("links.ts anchor not found — check upstream shape")
  }
  return src.replace(OLD, NEW)
}
