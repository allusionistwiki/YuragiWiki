import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { resolveRelative } from "../util/path"
import { formatDate } from "./Date"
import { JSX } from "preact"

interface Options {
  limit: number
}

export default ((opts?: Partial<Options>) => {
  const options: Options = { limit: 100, ...opts }

  const RecentUpdatesList: QuartzComponent = ({ fileData, allFiles, cfg }: QuartzComponentProps) => {
    const sorted = [...allFiles]
      .filter((f) => f.dates && f.slug && !f.slug.startsWith("tags/"))
      .sort((a, b) => {
        const aDate = a.dates?.modified?.getTime() ?? 0
        const bDate = b.dates?.modified?.getTime() ?? 0
        return bDate - aDate
      })
      .slice(0, options.limit)

    return (
      <div class="recent-updates-list">
        <p class="meta">最終更新日が新しい順に {sorted.length} 件表示</p>
        <ul class="section-ul">
          {sorted.map((page) => {
            const title = page.frontmatter?.title ?? page.slug
            const modified = page.dates?.modified
            return (
              <li class="section-li">
                <div class="section">
                  <p class="meta">
                    {modified && (
                      <time datetime={modified.toISOString()}>
                        {formatDate(modified, cfg.locale)}
                      </time>
                    )}
                  </p>
                  <div class="desc">
                    <h3>
                      <a href={resolveRelative(fileData.slug!, page.slug!)} class="internal">
                        {title}
                      </a>
                    </h3>
                  </div>
                </div>
              </li>
            )
          })}
        </ul>
      </div>
    )
  }

  RecentUpdatesList.css = `
    .recent-updates-list .section h3 {
      margin: 0;
    }
  `
  return RecentUpdatesList
}) satisfies QuartzComponentConstructor
