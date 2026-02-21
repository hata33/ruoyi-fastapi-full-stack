# 前端构建优化详解

## 1. Vite构建流程优化

```mermaid
flowchart TD
    Start([npm run build]) --> ViteParse[Vite解析配置]

    ViteParse --> ReadConfig[vite.config.js]
    ReadConfig --> LoadPlugins[加载插件]

    LoadPlugins --> PluginVue[@vitejs/plugin-vue]
    LoadPlugins --> PluginImport[plugin-auto-import]
    LoadPlugins --> PluginComponents[unplugin-vue-components]

    PluginVue --> DependencyPreBundle[依赖预构建]
    PluginImport --> DependencyPreBundle
    PluginComponents --> DependencyPreBundle

    DependencyPreBundle --> ScanDeps[扫描依赖]
    ScanDeps --> OptimizeDeps[优化依赖]

    OptimizeDeps --> ESBuild[esbuild转译]
    ESBuild --> BundleCode[打包代码]

    BundleCode --> CodeSplit[代码分割]
    CodeSplit --> SplitEntry[入口分割]
    CodeSplit --> SplitVendor[供应商分割]
    CodeSplit --> SplitAsync[异步分割]

    SplitEntry --> Minify[代码压缩]
    SplitVendor --> Minify
    SplitAsync --> Minify

    Minify --> Terser[Terser压缩]
    Terser --> TreeShake[Tree Shaking]

    TreeShake --> RemoveUnused[移除未使用代码]
    RemoveUnused --> GenerateAssets[生成资源]

    GenerateAssets --> Output[输出dist目录]
    Output --> Analyze[分析构建结果]

    style Start fill:#90EE90
    style Analyze fill:#4CAF50
    style DependencyPreBundle fill:#FF9800
```

## 2. 代码分割策略

```mermaid
flowchart TD
    Start([应用加载]) --> RouterConfig[路由配置]

    RouterConfig --> Strategy{分割策略}

    Strategy --> RouteLazy[路由懒加载]
    Strategy --> ComponentLazy[组件懒加载]
    Strategy --> VendorSplit[供应商分离]

    RouteLazy --> Import["import('/views/Home.vue')"]
    ComponentLazy --> DefineAsyncComponent
    VendorSplit --> ManualChunks

    Import --> GenerateChunk[生成独立chunk]
    DefineAsyncComponent --> GenerateChunk
    ManualChunks --> GenerateChunk

    GenerateChunk --> Chunk1[vendor.js]
    GenerateChunk --> Chunk2[common.js]
    GenerateChunk --> Chunk3[home.js]
    GenerateChunk --> Chunk4[about.js]
    GenerateChunk --> Chunk5[admin.js]

    Chunk1 --> Priority[优先级]
    Chunk2 --> Priority
    Chunk3 --> Priority
    Chunk4 --> Priority
    Chunk5 --> Priority

    Priority --> P1[预加载关键资源]
    Priority --> P2[按需加载]
    Priority --> P3[ prefetch预取]

    P1 --> Parallel[并行加载]
    P2 --> LazyLoad[懒加载]
    P3 --> Background[后台加载]

    Parallel --> Execute[执行]
    LazyLoad --> Execute
    Background --> Execute

    Execute --> Cache[缓存chunk]
    Cache --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style RouteLazy fill:#2196F3
```

## 3. 资源优化处理

```mermaid
flowchart TD
    Start([构建资源]) --> IdentifyType[识别类型]

    IdentifyType --> Images[图片资源]
    IdentifyType --> Fonts[字体资源]
    IdentifyType --> Styles[样式资源]
    IdentifyType --> Scripts[脚本资源]

    Images --> ImageOpt[图片优化]
    Fonts --> FontOpt[字体优化]
    Styles --> StyleOpt[样式优化]
    Scripts --> ScriptOpt[脚本优化]

    ImageOpt --> Compress[压缩图片]
    ImageOpt --> ConvertWebP[转换为WebP]
    ImageOpt --> GenerateSprite[生成雪碧图]

    Compress --> ImgResult
    ConvertWebP --> ImgResult
    GenerateSprite --> ImgResult

    FontOpt --> Subset[字体子集化]
    FontOpt --> WOFF2[转换为WOFF2]
    FontOpt --> CDN[字体CDN]

    Subset --> FontResult
    WOFF2 --> FontResult
    CDN --> FontResult

    StyleOpt --> PurgeCSS[移除未使用CSS]
    StyleOpt --> MinifyCSS[压缩CSS]
    StyleOpt --> CriticalCSS[提取关键CSS]

    PurgeCSS --> StyleResult
    MinifyCSS --> StyleResult
    CriticalCSS --> StyleResult

    ScriptOpt --> MinifyJS[压缩JS]
    ScriptOpt --> Polyfill[按需polyfill]
    ScriptOpt --> Babel[转译ES5]

    MinifyJS --> ScriptResult
    Polyfill --> ScriptResult
    Babel --> ScriptResult

    ImgResult --> Bundle[打包]
    FontResult --> Bundle
    StyleResult --> Bundle
    ScriptResult --> Bundle

    Bundle --> End([输出])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style ImageOpt fill:#FF9800
```

## 4. 缓存策略配置

```mermaid
flowchart TD
    Start([资源请求]) --> CheckCache{检查缓存}

    CheckCache -->|强缓存命中| ReturnStrong[返回强缓存]
    CheckCache -->|协商缓存| CheckETag[检查ETag]

    CheckCache -->|未命中| LoadResource[加载资源]

    ReturnStrong --> UseResource[使用资源]
    LoadResource --> SetCacheHeader[设置缓存头]

    SetCacheHeader --> CacheType{缓存类型}

    CacheType --> HashFilename["文件名hash<br/>app.a1b2c3.js"]
    CacheType --> CacheControl["Cache-Control<br/>max-age=31536000"]
    CacheType --> ETag["ETag指纹"]

    HashFilename --> CDN[CDN缓存]
    CacheControl --> Browser[浏览器缓存]
    ETag --> CheckETag

    CDN --> UpdateCheck{更新检查}
    Browser --> UpdateCheck
    CheckETag --> UpdateCheck

    UpdateCheck --> HashChanged{hash变化?}

    HashChanged -->|是| Invalidate[失效缓存]
    HashChanged -->|否| Validate[验证ETag]

    Invalidate --> DownloadNew[下载新资源]
    Validate --> ETagMatch{ETag匹配?}

    ETagMatch -->|是| Return304[返回304]
    ETagMatch -->|否| DownloadNew

    Return304 --> UseResource
    DownloadNew --> SetCacheHeader

    UseResource --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style CDN fill:#FF9800
```

## 5. 打包分析与优化

```mermaid
flowchart TD
    Start([构建完成]) --> RunAnalyzer[运行分析器]

    RunAnalyzer --> RollupPlugin[rollup-plugin-visualizer]
    RollupPlugin --> GenerateStats[生成统计]

    GenerateStats --> AnalyzeSize[分析体积]
    AnalyzeSize --> CheckModules[检查模块]

    CheckModules --> LargeModules[识别大模块]
    CheckModules --> Duplicate[重复依赖]
    CheckModules --> Unused[未使用代码]

    LargeModules --> Optimize1[优化策略]
    Duplicate --> Optimize2[去重策略]
    Unused --> Optimize3[移除策略]

    Optimize1 --> SplitExternal[外部化]
    Optimize1 --> LazyLoad[懒加载]
    Optimize1 --> CDNImport[CDN引入]

    Optimize2 --> Dedupe[依赖去重]
    Optimize2 --> Resolution[解析别名]

    Optimize3 --> TreeShake[Tree Shaking]
    Optimize3 --> Purge[PurgeCSS]

    SplitExternal --> ApplyOpt[应用优化]
    LazyLoad --> ApplyOpt
    CDNImport --> ApplyOpt
    Dedupe --> ApplyOpt
    Resolution --> ApplyOpt
    TreeShake --> ApplyOpt
    Purge --> ApplyOpt

    ApplyOpt --> Rebuild[重新构建]
    Rebuild --> CompareResults[对比结果]

    CompareResults --> Improved{有改善?}

    Improved -->|是| Satisfied[满意]
    Improved -->|否| Iterate[继续迭代]

    Satisfied --> Deploy[部署]
    Iterate --> RunAnalyzer

    Deploy --> End([完成])

    style Start fill:#90EE90
    style End fill:#4CAF50
    style RunAnalyzer fill:#2196F3
```

## 6. 按需自动导入

```mermaid
sequenceDiagram
    autonumber
    participant Dev as 👨‍💻 开发者
    participant Code as 📝 代码
    participant Plugin as 🔌 unplugin插件
    participant Scanner as 🔍 扫描器
    participant Builder as 🔨 构建器

    Dev->>Code: 编写代码
    Code->>Plugin: 检测到ref()

    Plugin->>Scanner: 扫描标识符
    Scanner->>Scanner: 识别API类型

    alt Vue API
        Scanner->>Plugin: 来自 'vue'
        Plugin->>Builder: 添加导入 "import { ref } from 'vue'"
    else VueRouter API
        Scanner->>Plugin: 来自 'vue-router'
        Plugin->>Builder: 添加路由导入
    else Element Plus
        Scanner->>Plugin: 来自 'element-plus'
        Plugin->>Builder: 添加组件导入
    end

    Builder->>Builder: 生成导入语句
    Builder->>Builder: 插入到文件顶部
    Builder-->>Code: 转换后的代码

    Code-->>Dev: 自动导入完成

    Note over Plugin: 无需手动import<br/>自动处理导入
```

## 7. 预渲染与SSG

```mermaid
flowchart TD
    Start([构建时]) --> GenerateRoutes[生成路由列表]

    GenerateRoutes --> ForEachRoute[遍历路由]

    ForEachRoute --> RenderRoute[渲染路由]
    RenderRoute --> LaunchServer[启动服务器]

    LaunchServer --> VisitPage[访问页面]
    VisitPage --> ExecuteApp[执行应用]

    ExecuteApp --> WaitForReady[等待就绪]
    WaitForReady --> Snapshot[快照HTML]

    Snapshot --> InjectMeta[注入元数据]
    InjectMeta --> WriteHTML[写入HTML]

    WriteHTML --> NextRoute{下一个路由?}
    NextRoute -->|是| ForEachRoute
    NextRoute -->|否| AllRoutes[所有路由完成]

    AllRoutes --> GenerateSitemap[生成sitemap]
    GenerateSitemap --> CopyAssets[复制静态资源]

    CopyAssets --> OutputDist[输出到dist]
    OutputDist --> Deploy[部署静态服务器]

    Deploy --> Nginx[Nginx/Apache]
    Deploy --> CDN[CDN]
    Deploy --> OSS[对象存储]

    Nginx --> Serve[服务静态文件]
    CDN --> Serve
    OSS --> Serve

    Serve --> UserVisit[用户访问]
    UserVisit --> ReturnHTML[返回HTML]
    ReturnHTML --> Hydrate[水合激活]

    Hydrate --> Interactive[可交互]

    style Start fill:#90EE90
    style Interactive fill:#4CAF50
    style RenderRoute fill:#FF9800
```

## 8. 性能监控与优化

```mermaid
mindmap
    root((前端性能优化))
        构建优化
            代码分割
            Tree Shaking
            压缩混淆
            依赖预构建
        加载优化
            懒加载
            预加载
            预连接
            资源优先级
        运行时优化
            虚拟列表
            防抖节流
            计算缓存
            keep-alive
        资源优化
            图片压缩
            字体子集
            CSS提取
            Gzip压缩
        缓存策略
            强缓存
            协商缓存
            LocalStorage
            Service Worker
        监控指标
            FCP首次绘制
            LCP最大内容
            FID首次输入
            CLS布局偏移
            TTI可交互时间
```

## 关键配置文件

| 文件 | 用途 |
|------|------|
| `vite.config.js` | Vite构建配置 |
| `.eslintrc.js` | ESLint代码检查 |
| `.prettierrc` | Prettier格式化 |
| `package.json` | 依赖与脚本 |
| `postcss.config.js` | PostCSS配置 |

## 最佳实践

```mermaid
flowchart LR
    subgraph "构建阶段"
        A1[分析构建结果]
        A2[识别瓶颈]
        A3[优化策略]
        A4[验证效果]
    end

    subgraph "运行阶段"
        B1[性能监控]
        B2[收集指标]
        B3[分析问题]
        B4[持续改进]
    end

    subgraph "部署阶段"
        C1[CDN加速]
        C2[Gzip压缩]
        C3[缓存策略]
        C4[渐进增强]
    end

    A1 --> Practice[实施]
    B1 --> Practice
    C1 --> Practice

    style A1 fill:#4CAF50
    style B1 fill:#FF9800
    style C1 fill:#2196F3
```
