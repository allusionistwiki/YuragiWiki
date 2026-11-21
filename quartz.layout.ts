import { PageLayout, SharedLayout } from "./quartz/cfg"
import * as Component from "./quartz/components"
import CreatedModifiedMeta from "./quartz/components/CreatedModifiedMeta"
import { FileTrieNode } from "./quartz/util/fileTrie"

// 層セクション構成（/L1/ /L2/ /layers/）: 全サブツリーをサイドバーに表示する
// （セクション内では explorer.inline.ts の section scoping で当該セクションのみになる）。
const explorerOptions = {
  // モバイル（iOS）対策: 初期は畳み、タップ開封時の 1 展開も最上位節のみで
  // 数千ノードの DOM 生成を防止（開封は toggleAll で全展開可）。
  folderDefaultState: "collapsed" as const,
  folderClickBehavior: "collapse" as const,
  filterFn: (node: FileTrieNode) => node.slugSegment !== "tags",
  mapFn: (node: FileTrieNode) => {
    // 節名の和文表示（Explorer のツリーはスラッグ表示のままなので display 名を付与）。
    // mapFn は toString してクライアントへシリアライズされるため、外側変数を閉じないこと（必須）。
    const LABELS: Record<string, string> = {
      units: "篇記事（L1 版）",
      full: "原文全文版",
      free: "自由記述版",
      entities: "実体索引",
      topics: "話題索引",
      authors: "投稿者索引",
      works: "作品ページ",
      works_index: "創作類型索引",
      widx_authors: "創作作者索引",
      widx_units: "創作篇収容索引",
      flicker: "日記（Flicker）",
      static: "static",
    }
    if (LABELS[node.slugSegment]) {
      node.displayName = LABELS[node.slugSegment]
    }
    if (node.children.length > 40) {
      node.collapsed = true
      node.children = []
    }
    return node
  },
}

// components shared across all pages
export const sharedPageComponents: SharedLayout = {
  head: Component.Head(),
  header: [],
  afterBody: [Component.Search({ enablePreview: false })],
  footer: Component.Footer({
    links: {
      "YuragiWiki repo（原文コーパス）": "https://github.com/allusionistwiki/YuragiWiki",
      "解析パイプライン（work）": "https://github.com/allusionistwiki/AllusionistWiki_work",
      "AllusionistWiki portal": "https://allusionistwiki.github.io/",
      "Quartz プロジェクト": "https://github.com/jackyzha0/quartz",
    },
  }),
}

// components for pages that display a single page (e.g. a single note)
export const defaultContentPageLayout: PageLayout = {
  beforeBody: [
    Component.ConditionalRender({
      component: Component.Breadcrumbs(),
      condition: (page) => page.fileData.slug !== "index",
    }),
    Component.ArticleTitle(),
    CreatedModifiedMeta(),
    Component.TagList(),
  ],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Flex({
      components: [
        {
          Component: Component.Search(),
          grow: true,
        },
        { Component: Component.Darkmode() },
        { Component: Component.ReaderMode() },
      ],
    }),
    Component.Explorer(explorerOptions),
  ],
  right: [
    Component.DesktopOnly(Component.TableOfContents()),
    Component.Backlinks(),
  ],
}

// components for pages that display lists of pages  (e.g. tags or folders)
export const defaultListPageLayout: PageLayout = {
  beforeBody: [Component.Breadcrumbs(), Component.ArticleTitle(), CreatedModifiedMeta()],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Flex({
      components: [
        {
          Component: Component.Search(),
          grow: true,
        },
        { Component: Component.Darkmode() },
      ],
    }),
    Component.Explorer(explorerOptions),
  ],
  right: [],
}
