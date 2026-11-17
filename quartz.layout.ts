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
  afterBody: [],
  footer: Component.Footer({
    links: {
      "Obsidian vault（ソース）": "https://github.com/allusionistwiki/AllusionistLLMWiki2_Obsidian",
      "Quartz プロジェクト": "https://github.com/allusionistwiki/AllusionistWiki2",
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
    Component.Graph(),
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
