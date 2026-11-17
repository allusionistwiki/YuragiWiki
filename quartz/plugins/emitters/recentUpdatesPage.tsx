import { QuartzEmitterPlugin } from "../types"
import { QuartzComponentProps } from "../../components/types"
import HeaderConstructor from "../../components/Header"
import BodyConstructor from "../../components/Body"
import { pageResources, renderPage } from "../../components/renderPage"
import { QuartzPluginData, defaultProcessedContent } from "../vfile"
import { FullPageLayout } from "../../cfg"
import { FullSlug, pathToRoot } from "../../util/path"
import { sharedPageComponents, defaultListPageLayout } from "../../../quartz.layout"
import { write } from "./helpers"
import { BuildCtx } from "../../util/ctx"
import { StaticResources } from "../../util/resources"
import RecentUpdatesList from "../../components/RecentUpdatesList"

interface RecentUpdatesOptions extends FullPageLayout {
  limit?: number
}

export const RecentUpdatesPage: QuartzEmitterPlugin<Partial<RecentUpdatesOptions>> = (userOpts) => {
  const limit = userOpts?.limit ?? 100
  const opts: FullPageLayout = {
    ...sharedPageComponents,
    ...defaultListPageLayout,
    pageBody: RecentUpdatesList({ limit }),
    ...userOpts,
  }

  const { head: Head, header, beforeBody, pageBody, afterBody, left, right, footer: Footer } = opts
  const Header = HeaderConstructor()
  const Body = BodyConstructor()

  return {
    name: "RecentUpdatesPage",
    getQuartzComponents() {
      return [
        Head,
        Header,
        Body,
        ...header,
        ...beforeBody,
        pageBody,
        ...afterBody,
        ...left,
        ...right,
        Footer,
      ]
    },
    async *emit(ctx, content, resources) {
      const allFiles = content.map((c) => c[1].data)
      const cfg = ctx.cfg.configuration
      const slug = "recent-updates" as FullSlug

      const [tree, file] = defaultProcessedContent({
        slug,
        frontmatter: {
          title: "直近更新記事",
          description: "最終更新日が新しい順に1000件表示（自動生成）",
        },
      })

      const externalResources = pageResources(pathToRoot(slug), resources)
      const componentData: QuartzComponentProps = {
        ctx,
        fileData: file.data,
        externalResources,
        cfg,
        children: [],
        tree,
        allFiles,
      }

      const pageContent = renderPage(cfg, slug, componentData, opts, externalResources)
      yield write({
        ctx,
        content: pageContent,
        slug,
        ext: ".html",
      })
    },
  }
}
