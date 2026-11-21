import { QuartzConfig } from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"

/**
 * Quartz 4 Configuration
 *
 * See https://quartz.jzhao.xyz/configuration for more information.
 */
const config: QuartzConfig = {
  configuration: {
    pageTitle: "ゆらぎの神話 BBS 実況 Wiki",
    pageTitleSuffix: " | ゆらぎの神話 Wiki",
    enableSPA: false,
    // popovers（hover プレビュー）は「勝手に飛ぶ」知覚と iOS 負荷により無効（v1/v2 恒久準拠）
    enablePopovers: false,
    analytics: {
      provider: null,
    },
    locale: "ja-JP",
    baseUrl: "allusionistwiki.github.io/YuragiWiki",
    ignorePatterns: ["private", "templates", ".obsidian"],
    defaultDateType: "modified",
    theme: {
      fontOrigin: "googleFonts",
      cdnCaching: true,
      typography: {
        // 和文主体のコーパス: 日本語 webfont を明示指定（旧指定は欧文字のみで
        // 本文が OS 既定フォールバックだった）。italic 非対応和文フォントへの
        // ital 要求は Google Fonts css2 が 400 を返し stylesheet ごと失効するため
        // includeItalic: false + 実在 wght のみ指定（必須）。
        header: { name: "Zen Kaku Gothic New", weights: [400, 500, 700], includeItalic: false },
        body: { name: "Noto Sans JP", weights: [400, 500, 700], includeItalic: false },
        code: { name: "IBM Plex Mono", weights: [400, 600] },
      },
      colors: {
        // 和紙×藍×松緑の配色（light=和紙基調、dark=藍墨）
        lightMode: {
          light: "#f8f6f1",
          lightgray: "#eae5db",
          gray: "#b3ab9e",
          darkgray: "#4c463e",
          dark: "#24211c",
          secondary: "#2f5d78",
          tertiary: "#7d9a8c",
          highlight: "rgba(125, 154, 140, 0.16)",
          textHighlight: "#ffe9a8",
        },
        darkMode: {
          light: "#191b1f",
          lightgray: "#2a2d33",
          gray: "#5f636b",
          darkgray: "#d1ccc3",
          dark: "#f0ece3",
          secondary: "#9ec1da",
          tertiary: "#93b2a3",
          highlight: "rgba(158, 193, 218, 0.15)",
          textHighlight: "#c9a22788",
        },
      },
    },
  },
  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({
        priority: ["frontmatter", "git", "filesystem"],
      }),
      Plugin.SyntaxHighlighting({
        theme: {
          light: "github-light",
          dark: "github-dark",
        },
        keepBackground: false,
      }),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlEmbed: false }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents(),
      Plugin.CrawlLinks({ markdownLinkResolution: "shortest" }),
      Plugin.Description(),
      Plugin.Latex({ renderEngine: "katex" }),
    ],
    filters: [Plugin.RemoveDrafts()],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({
        enableSiteMap: true,
        enableRSS: true,
        // 大量ミラーページ（記事・全文）を contentIndex・sitemap・RSS から除外
        // （v2 実務準拠: 全ページ load での巨大化・iOS メモリ対策）。
        excludePrefixes: ["full/", "works/", "works_index/", "widx_authors/", "widx_units/"],
        excerptChars: 200,
      }),
      Plugin.RecentUpdatesPage({ limit: 1000 }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.Favicon(),
      Plugin.NotFoundPage(),
      // Comment out CustomOgImages to speed up build time
      // CustomOgImages は全ページ分の OG 画像を satori/resvg で描くためビルド時間の大半を占める。OG画像なしで運用（v2 実測: 9分→40秒）
      // Plugin.CustomOgImages(),
    ],
  },
}

export default config
