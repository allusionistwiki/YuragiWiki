import sourceMapSupport from "source-map-support"
sourceMapSupport.install(options)
import path from "path"
import { PerfTimer } from "./util/perf"
import { rm } from "fs/promises"
import { GlobbyFilterFunction, isGitIgnored } from "globby"
import { styleText } from "util"
import { parseMarkdown } from "./processors/parse"
import { filterContent } from "./processors/filter"
import { emitContent } from "./processors/emit"
import cfg from "../quartz.config"
import { FilePath, FullSlug, joinSegments, slugifyFilePath } from "./util/path"
import { existsSync, mkdirSync, readFileSync, writeFileSync, createReadStream, createWriteStream } from "node:fs"
import { createHash } from "crypto"
import { createGzip, createGunzip } from "node:zlib"
import { createInterface } from "node:readline"
import rfdc from "rfdc"
import chokidar from "chokidar"
import { ProcessedContent } from "./plugins/vfile"
import { Argv, BuildCtx } from "./util/ctx"
import { glob, toPosixPath } from "./util/glob"
import { trace } from "./util/trace"
import { options } from "./util/sourcemap"
import { Mutex } from "async-mutex"
import { getStaticResourcesFromPlugins } from "./plugins"
import { randomIdNonSecure } from "./util/random"
import { ChangeEvent } from "./plugins/types"
import { minimatch } from "minimatch"

type ContentMap = Map<
  FilePath,
  | {
      type: "markdown"
      content: ProcessedContent
    }
  | {
      type: "other"
    }
>

type BuildData = {
  ctx: BuildCtx
  ignored: GlobbyFilterFunction
  mut: Mutex
  contentMap: ContentMap
  changesSinceLastBuild: Record<FilePath, ChangeEvent["type"]>
  lastBuildMs: number
}

async function buildQuartz(argv: Argv, mut: Mutex, clientRefresh: () => void) {
  const ctx: BuildCtx = {
    buildId: randomIdNonSecure(),
    argv,
    cfg,
    allSlugs: [],
    allFiles: [],
    incremental: false,
  }

  const perf = new PerfTimer()
  const output = argv.output

  const pluginCount = Object.values(cfg.plugins).flat().length
  const pluginNames = (key: "transformers" | "filters" | "emitters") =>
    cfg.plugins[key].map((plugin) => plugin.name)
  if (argv.verbose) {
    console.log(`Loaded ${pluginCount} plugins`)
    console.log(`  Transformers: ${pluginNames("transformers").join(", ")}`)
    console.log(`  Filters: ${pluginNames("filters").join(", ")}`)
    console.log(`  Emitters: ${pluginNames("emitters").join(", ")}`)
  }

  const release = await mut.acquire()
  perf.addEvent("clean")
  if (process.env.QUARTZ_SKIP_CLEAN === "1") {
    console.log(`Skipped cleaning output directory \`${output}\` (diff build)`)
  } else {
    await rm(output, { recursive: true, force: true })
    console.log(`Cleaned output directory \`${output}\` in ${perf.timeSince("clean")}`)
  }

  perf.addEvent("glob")
  const allFiles = await glob("**/*.*", argv.directory, cfg.configuration.ignorePatterns)
  const markdownPaths = allFiles.filter((fp) => fp.endsWith(".md")).sort()
  console.log(
    `Found ${markdownPaths.length} input files from \`${argv.directory}\` in ${perf.timeSince("glob")}`,
  )

  const filePaths = markdownPaths.map((fp) => joinSegments(argv.directory, fp) as FilePath)
  ctx.allFiles = allFiles
  ctx.allSlugs = allFiles.map((fp) => slugifyFilePath(fp as FilePath))

  const prevManifest = process.env.QUARTZ_PREV_MANIFEST
  const diffMode = process.env.QUARTZ_DIFF === "1" && !!prevManifest && existsSync(prevManifest)
  const parsedFiles = diffMode
    ? await parseIncremental(ctx, filePaths)
    : await parseMarkdown(ctx, filePaths)
  const filteredContent = filterContent(ctx, parsedFiles)

  await emitContent(ctx, filteredContent)
  await writeDiffState(ctx, filteredContent)
  console.log(
    styleText("green", `Done processing ${markdownPaths.length} files in ${perf.timeSince()}`),
  )
  release()

  if (argv.watch) {
    ctx.incremental = true
    return startWatching(ctx, mut, parsedFiles, clientRefresh)
  }
}

// CI 差分ビルド（QUARTZ_DIFF=1 のときだけ）: manifest の sha256 と比べ、
// 変更された .md だけ parse（LLM）し、未変更ページは processed キャッシュから
// 復元して合流する。emit は全数（出力は完全一致・graph/search も毎回最新）。
const DIFF_PAGES: Record<string, string> = {}

function relOf(ctx: BuildCtx, fp: FilePath): string {
  return path.relative(ctx.argv.directory, fp).split(path.sep).join("/")
}

async function parseIncremental(ctx: BuildCtx, filePaths: FilePath[]) {
  const { argv } = ctx
  const prevRaw = JSON.parse(readFileSync(process.env.QUARTZ_PREV_MANIFEST!, "utf8"))
  const prevPages: Record<string, string> = prevRaw?.pages ?? {}
  if (prevRaw?.manifestVersion !== 2) {
    throw new Error("diff build: prev manifest is not manifestVersion 2 — full build required")
  }

  const changedPaths: FilePath[] = []
  const changedRels = new Set<string>()
  for (const fp of filePaths) {
    const rel = relOf(ctx, fp)
    const hash = createHash("sha256").update(readFileSync(fp)).digest("hex")
    DIFF_PAGES[rel] = hash
    if (prevPages[rel] !== hash) {
      changedPaths.push(fp)
      changedRels.add(rel)
    }
  }
  console.log(`diff: pages=${filePaths.length} llm-parse=${changedPaths.length}`)

  const cachePath = process.env.QUARTZ_PROCESSED_CACHE ?? ".quartz-cache/processed.jsonl.gz"
  if (!existsSync(cachePath)) {
    throw new Error(`diff build: processed cache missing at ${cachePath} — full build required`)
  }
  // processed スナップショットは JSONL（1 ページ 1 行 gzip）なのでストリームで
  // 1 行ずつ読む（JSON.parse 単発は V8 の 512MB 文字列/バッファ上限に当たる）。
  const cacheLines: string[] = []
  {
    const rl = createInterface({
      input: createReadStream(cachePath).pipe(createGunzip()),
      crlfDelay: Infinity,
    })
    for await (const line of rl) {
      if (line.trim() === "") continue
      cacheLines.push(line)
    }
  }
  // キャッシュが未変更全数をカバーしない（古い・部分的）なら差分ビルドの
  // 利点がないので full parse へ完全退避する（restored+parsed >= pages を保証）。
  if (cacheLines.length < filePaths.length - changedPaths.length) {
    console.log(
      styleText(
        "yellow",
        `diff: processed cache covers ${cacheLines.length} < ${filePaths.length - changedPaths.length} unchanged pages — falling back to full parse`,
      ),
    )
    const parsedAll = await parseMarkdown(ctx, filePaths)
    for (const fp of filePaths) {
      DIFF_PAGES[relOf(ctx, fp)] = createHash("sha256").update(readFileSync(fp)).digest("hex")
    }
    return parsedAll
  }
  const cached: { pages?: any[] } = { pages: [] }
  for (const line of cacheLines) {
    cached.pages!.push(JSON.parse(line))
  }
  const parsedNew = await parseMarkdown(ctx, changedPaths)
  const DATE_KEYS = ["date", "modified", "published", "created"]
  const merged: ProcessedContent[] = [...parsedNew]
  for (const e of cached.pages ?? []) {
    if (changedRels.has(e.rel)) continue
    // 未変更ページは前回の processed（frontmatter・HTML・tree 込みの data）を
    // そのまま使う — parse は二度と同じ結果になるため LLM を走らせない。
    // JSON 往復で Date に化けた日付フィールドを復元する（contentIndex 等の
    // toISOString 呼び出しが Date を前提にするため）。CreatedModifiedDate が
    // 書き込む data.dates.{created,modified,published} と top-level 日付の両方。
    for (const k of DATE_KEYS) {
      if (typeof e.data?.[k] === "string") {
        e.data[k] = new Date(e.data[k])
      }
    }
    if (e.data?.dates) {
      for (const k of ["created", "modified", "published"]) {
        if (typeof e.data.dates[k] === "string") {
          e.data.dates[k] = new Date(e.data.dates[k])
        }
      }
    }
    const clone: any = rfdc()
    const root: any = clone(e.data.htmlAst)
    root.type = "root"
    const vfile: any = {
      value: e.value,
      data: e.data,
      messages: [],
    }
    vfile.data.tree = root
    merged.push([root, vfile] as unknown as ProcessedContent)
  }
  console.log(`diff: restored=${merged.length - parsedNew.length} parsed=${parsedNew.length}`)
  return merged
}

// 差分状態（manifest v2 + processed キャッシュ）を emit 後に更新する。
// 通常（フル）ビルドでも呼ばれる — 次回の差分ビルドの基準（キャッシュ）を
// 暖める。差分モードでは parseIncremental が計算した sha マップをそのまま使う。
// 途中失敗で書かれなくても次回の差分計算は安全（変更は再検出される）。
async function writeDiffState(ctx: BuildCtx, filteredContent: ProcessedContent[]) {
  const { argv } = ctx
  if (Object.keys(DIFF_PAGES).length === 0) {
    for (const rel0 of ctx.allFiles) {
      if (!rel0.endsWith(".md")) continue
      const rel = rel0.split("\\").join("/")
      DIFF_PAGES[rel] = createHash("sha256").update(readFileSync(joinSegments(argv.directory, rel0))).digest("hex")
    }
  }
  const manifestPath = joinSegments(argv.output, "index.json") as FilePath
  writeFileSync(manifestPath, JSON.stringify({ manifestVersion: 2, pages: DIFF_PAGES }))

  const cachePath = process.env.QUARTZ_PROCESSED_CACHE ?? ".quartz-cache/processed.jsonl.gz"
  // processed スナップショットは JSONL（1 ページ 1 行）で書く。単発 JSON.stringify は
  // 全ページの AST で V8 の文字列上限（約 512MB）を超えるためストリームで出力する。
  mkdirSync(path.dirname(cachePath), { recursive: true })
  const out = createWriteStream(cachePath)
  const gz = createGzip()
  gz.pipe(out)
  for (const content of filteredContent) {
    const vf = content[1]
    gz.write(JSON.stringify({ rel: vf.data.relativePath, value: String(vf.value), data: vf.data }) + "\n")
  }
  await new Promise<void>((resolve, reject) => {
    gz.on("error", reject)
    out.on("error", reject)
    out.on("finish", resolve)
    gz.end()
  })
  console.log(`diff: state written pages=${filteredContent.length}`)
}

// setup watcher for rebuilds
async function startWatching(
  ctx: BuildCtx,
  mut: Mutex,
  initialContent: ProcessedContent[],
  clientRefresh: () => void,
) {
  const { argv, allFiles } = ctx

  const contentMap: ContentMap = new Map()
  for (const filePath of allFiles) {
    contentMap.set(filePath, {
      type: "other",
    })
  }

  for (const content of initialContent) {
    const [_tree, vfile] = content
    contentMap.set(vfile.data.relativePath!, {
      type: "markdown",
      content,
    })
  }

  const gitIgnoredMatcher = await isGitIgnored()
  const buildData: BuildData = {
    ctx,
    mut,
    contentMap,
    ignored: (fp) => {
      const pathStr = toPosixPath(fp.toString())
      if (pathStr.startsWith(".git/")) return true
      if (gitIgnoredMatcher(pathStr)) return true
      for (const pattern of cfg.configuration.ignorePatterns) {
        if (minimatch(pathStr, pattern)) {
          return true
        }
      }

      return false
    },

    changesSinceLastBuild: {},
    lastBuildMs: 0,
  }

  const watcher = chokidar.watch(".", {
    persistent: true,
    cwd: argv.directory,
    ignoreInitial: true,
  })

  const changes: ChangeEvent[] = []
  watcher
    .on("add", (fp) => {
      fp = toPosixPath(fp)
      if (buildData.ignored(fp)) return
      changes.push({ path: fp as FilePath, type: "add" })
      void rebuild(changes, clientRefresh, buildData)
    })
    .on("change", (fp) => {
      fp = toPosixPath(fp)
      if (buildData.ignored(fp)) return
      changes.push({ path: fp as FilePath, type: "change" })
      void rebuild(changes, clientRefresh, buildData)
    })
    .on("unlink", (fp) => {
      fp = toPosixPath(fp)
      if (buildData.ignored(fp)) return
      changes.push({ path: fp as FilePath, type: "delete" })
      void rebuild(changes, clientRefresh, buildData)
    })

  return async () => {
    await watcher.close()
  }
}

async function rebuild(changes: ChangeEvent[], clientRefresh: () => void, buildData: BuildData) {
  const { ctx, contentMap, mut, changesSinceLastBuild } = buildData
  const { argv, cfg } = ctx

  const buildId = randomIdNonSecure()
  ctx.buildId = buildId
  buildData.lastBuildMs = new Date().getTime()
  const numChangesInBuild = changes.length
  const release = await mut.acquire()

  // if there's another build after us, release and let them do it
  if (ctx.buildId !== buildId) {
    release()
    return
  }

  const perf = new PerfTimer()
  perf.addEvent("rebuild")
  console.log(styleText("yellow", "Detected change, rebuilding..."))

  // update changesSinceLastBuild
  for (const change of changes) {
    changesSinceLastBuild[change.path] = change.type
  }

  const staticResources = getStaticResourcesFromPlugins(ctx)
  const pathsToParse: FilePath[] = []
  for (const [fp, type] of Object.entries(changesSinceLastBuild)) {
    if (type === "delete" || path.extname(fp) !== ".md") continue
    const fullPath = joinSegments(argv.directory, toPosixPath(fp)) as FilePath
    pathsToParse.push(fullPath)
  }

  const parsed = await parseMarkdown(ctx, pathsToParse)
  for (const content of parsed) {
    contentMap.set(content[1].data.relativePath!, {
      type: "markdown",
      content,
    })
  }

  // update state using changesSinceLastBuild
  // we do this weird play of add => compute change events => remove
  // so that partialEmitters can do appropriate cleanup based on the content of deleted files
  for (const [file, change] of Object.entries(changesSinceLastBuild)) {
    if (change === "delete") {
      // universal delete case
      contentMap.delete(file as FilePath)
    }

    // manually track non-markdown files as processed files only
    // contains markdown files
    if (change === "add" && path.extname(file) !== ".md") {
      contentMap.set(file as FilePath, {
        type: "other",
      })
    }
  }

  const changeEvents: ChangeEvent[] = Object.entries(changesSinceLastBuild).map(([fp, type]) => {
    const path = fp as FilePath
    const processedContent = contentMap.get(path)
    if (processedContent?.type === "markdown") {
      const [_tree, file] = processedContent.content
      return {
        type,
        path,
        file,
      }
    }

    return {
      type,
      path,
    }
  })

  // update allFiles and then allSlugs with the consistent view of content map
  ctx.allFiles = Array.from(contentMap.keys())
  ctx.allSlugs = ctx.allFiles.map((fp) => slugifyFilePath(fp as FilePath))
  let processedFiles = filterContent(
    ctx,
    Array.from(contentMap.values())
      .filter((file) => file.type === "markdown")
      .map((file) => file.content),
  )

  let emittedFiles = 0
  for (const emitter of cfg.plugins.emitters) {
    // Try to use partialEmit if available, otherwise assume the output is static
    const emitFn = emitter.partialEmit ?? emitter.emit
    const emitted = await emitFn(ctx, processedFiles, staticResources, changeEvents)
    if (emitted === null) {
      continue
    }

    if (Symbol.asyncIterator in emitted) {
      // Async generator case
      for await (const file of emitted) {
        emittedFiles++
        if (ctx.argv.verbose) {
          console.log(`[emit:${emitter.name}] ${file}`)
        }
      }
    } else {
      // Array case
      emittedFiles += emitted.length
      if (ctx.argv.verbose) {
        for (const file of emitted) {
          console.log(`[emit:${emitter.name}] ${file}`)
        }
      }
    }
  }

  console.log(`Emitted ${emittedFiles} files to \`${argv.output}\` in ${perf.timeSince("rebuild")}`)
  console.log(styleText("green", `Done rebuilding in ${perf.timeSince()}`))
  changes.splice(0, numChangesInBuild)
  clientRefresh()
  release()
}

export default async (argv: Argv, mut: Mutex, clientRefresh: () => void) => {
  try {
    return await buildQuartz(argv, mut, clientRefresh)
  } catch (err) {
    trace("\nExiting Quartz due to a fatal error", err as Error)
  }
}
