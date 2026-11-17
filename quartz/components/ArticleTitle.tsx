import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
import { trieFromAllFiles } from "../util/ctx"

const ArticleTitle: QuartzComponent = ({ fileData, displayClass, ctx, allFiles }: QuartzComponentProps) => {
  let title = fileData.frontmatter?.title

  // フォルダindexページ（index.md / _index.md、または _index.md が無い自動生成フォルダページ）は、
  // frontmatter title がファイル名由来のプレースホルダ（"index" / "_index" / "フォルダ: ..."）の場合、
  // trie の日本語表示名（FOLDER_DISPLAY_NAMES）を使う。
  const slug = fileData.slug
  if (slug && (slug === "index" || slug.endsWith("/index"))) {
    const folderSlug = slug === "index" ? "" : slug.slice(0, -"/index".length)
    const folderPath = folderSlug.split("/").filter(Boolean)
    const isPlaceholder =
      title === "index" || title === "_index" || (title?.startsWith("フォルダ:") ?? false)
    if (folderPath.length > 0 && isPlaceholder) {
      const trie = (ctx.trie ??= trieFromAllFiles(allFiles))
      const node = trie.findNode(folderPath)
      if (node && node.displayName) {
        title = node.displayName
      }
    }
  }

  if (title) {
    return <h1 class={classNames(displayClass, "article-title")}>{title}</h1>
  } else {
    return null
  }
}

ArticleTitle.css = `
.article-title {
  margin: 2rem 0 0 0;
}
`

export default (() => ArticleTitle) satisfies QuartzComponentConstructor
