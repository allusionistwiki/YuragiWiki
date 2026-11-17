import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import style from "./styles/backlinks.scss"
import { resolveRelative, simplifySlug } from "../util/path"
import { i18n } from "../i18n"
import { classNames } from "../util/lang"
import OverflowListFactory from "./OverflowList"

interface BacklinksOptions {
  hideWhenEmpty: boolean
}

const defaultOptions: BacklinksOptions = {
  hideWhenEmpty: true,
}

// 自動生成ページ・index系・log・status はバックリンクの対象外。
// 対象ページ自体の表示と、他ページへの表示の両方を除外する。
// group（terminology/groups/*）は index ではないため除外しない。
function isExcludedFromBacklinks(slug: SimpleSlug): boolean {
  if (slug === "recent-updates" || slug === "recent-commits") return true
  if (slug === "index" || slug.endsWith("/index")) return true
  if (slug === "log" || slug === "status") return true
  return false
}

export default ((opts?: Partial<BacklinksOptions>) => {
  const options: BacklinksOptions = { ...defaultOptions, ...opts }
  const { OverflowList, overflowListAfterDOMLoaded } = OverflowListFactory()

  const Backlinks: QuartzComponent = ({
    fileData,
    allFiles,
    displayClass,
    cfg,
  }: QuartzComponentProps) => {
    const slug = simplifySlug(fileData.slug!)
    // 対象ページ自体にはバックリンクセクションを表示しない
    if (isExcludedFromBacklinks(slug)) {
      return null
    }
    // 対象ページを他ページのバックリンク一覧から除外する
    const backlinkFiles = allFiles.filter(
      (file) =>
        file.links?.includes(slug) && !isExcludedFromBacklinks(simplifySlug(file.slug!)),
    )
    if (options.hideWhenEmpty && backlinkFiles.length == 0) {
      return null
    }
    return (
      <div class={classNames(displayClass, "backlinks")}>
        <h3>{i18n(cfg.locale).components.backlinks.title}</h3>
        <OverflowList>
          {backlinkFiles.length > 0 ? (
            backlinkFiles.map((f) => (
              <li>
                <a href={resolveRelative(fileData.slug!, f.slug!)} class="internal">
                  {f.frontmatter?.title}
                </a>
              </li>
            ))
          ) : (
            <li>{i18n(cfg.locale).components.backlinks.noBacklinksFound}</li>
          )}
        </OverflowList>
      </div>
    )
  }

  Backlinks.css = style
  Backlinks.afterDOMLoaded = overflowListAfterDOMLoaded

  return Backlinks
}) satisfies QuartzComponentConstructor
