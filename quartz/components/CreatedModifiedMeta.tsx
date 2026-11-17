import { formatDate } from "./Date"
import { QuartzComponentConstructor, QuartzComponentProps } from "./types"
import readingTime from "reading-time"
import { classNames } from "../util/lang"
import { i18n } from "../i18n"
import { JSX } from "preact"
import style from "./styles/createdModifiedMeta.scss"

interface ContentMetaOptions {
  /**
   * Whether to display reading time
   */
  showReadingTime: boolean
  /**
   * Whether to display the created date
   */
  showCreated: boolean
  /**
   * Whether to display the modified date
   */
  showModified: boolean
}

const defaultOptions: ContentMetaOptions = {
  showReadingTime: true,
  showCreated: true,
  showModified: true,
}

export default ((opts?: Partial<ContentMetaOptions>) => {
  const options: ContentMetaOptions = { ...defaultOptions, ...opts }

  function ContentMetadata({ cfg, fileData, displayClass }: QuartzComponentProps) {
    const text = fileData.text

    if (text) {
      const segments: (string | JSX.Element)[] = []

      if (fileData.dates) {
        const { created, modified } = fileData.dates
        const sameDay = created.getTime() === modified.getTime()

        if (options.showCreated) {
          segments.push(
            <span>
              作成 <time datetime={created.toISOString()}>{formatDate(created, cfg.locale)}</time>
            </span>,
          )
        }
        if (options.showModified && !sameDay) {
          segments.push(
            <span>
              最終更新 <time datetime={modified.toISOString()}>{formatDate(modified, cfg.locale)}</time>
            </span>,
          )
        }
      }

      if (options.showReadingTime) {
        const { minutes } = readingTime(text)
        const displayedTime = i18n(cfg.locale).components.contentMeta.readingTime({
          minutes: Math.ceil(minutes),
        })
        segments.push(<span>{displayedTime}</span>)
      }

      return (
        <p class={classNames(displayClass, "content-meta")}>
          {segments.map((seg, i) => (
            <span key={i} class="content-meta-segment">
              {seg}
            </span>
          ))}
        </p>
      )
    } else {
      return null
    }
  }

  ContentMetadata.css = style
  return ContentMetadata
}) satisfies QuartzComponentConstructor
