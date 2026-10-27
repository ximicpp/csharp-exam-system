# 选择题数据与验证约定

题库基线：.NET 10 / C# 14；受众：资深 Python / C++ 工程师。所有题目必须是四选项的单选题，恰有一个正确答案，围绕实际编码、排障或设计判断，排除版本年份、冷僻语法和精确性能数字的记忆题。

七个 JSON 文件分别保存 Q01–Q20（types）、Q21–Q40（execution）、Q41–Q60（runtime）、Q61–Q80（foundations）、Q81–Q100（modeling）、Q101–Q120（queries）及 Q121–Q240（microsoft）。前六组构成迁移题库，microsoft 是独立配套卷；顶层均为题目数组。每题字段：

```json
{
  "id": "Q01",
  "title": "简短标题",
  "kind": "single",
  "tier": "core",
  "topics": ["值复制"],
  "scenario": "作答必需的业务约束；不需要时使用空字符串。",
  "prompt": "明确前提和具体问题，不依赖答案中的补充前提。",
  "code": [{"path": "tests/Quiz.Checks/Types.cs", "region": "Q01"}],
  "options": {"A": "选项", "B": "选项", "C": "选项", "D": "选项"},
  "answers": ["B"],
  "rationale": {"A": "错因", "B": "正确理由", "C": "错因", "D": "错因"},
  "takeaway": "这道题应引导的学习内容与实际使用边界。",
  "learn": ["docs/02-values.md"],
  "sources": [{"title": "Microsoft Learn 标题", "url": "https://learn.microsoft.com/..."}],
  "verification": {"kind": "runtime", "checks": ["Q01"], "note": "实际验证哪些结论，以及不能由实验推广的部分。"}
}
```

`kind` 只能为 `single`，`answers` 必须恰含一个选项；`tier` 为 `core` 或 `deep`，不是计时或认证等级。题干给出足以唯一作答的前提，四项逐项解释；不能把多个正确陈述原样保留后只删答案，也不使用组合选项或“以上皆是”伪装单选。`code` 可以为空；题面中的代码必须由源码区域生成，不在 JSON 中重复粘贴。源码用唯一的 `#region Q01` / `#endregion` 包围连续片段，需要类型和调用时使用多个区域如 Q01-types、Q01-call。题面不能展示直接揭示答案的验收断言。

`scenario` 字段保留，允许 `""`；没有额外约束的代码结果题直接给题干与代码。场景只保留影响作答的输入、资源所有权、并发交错、协议或部署需求，不把错误设想写成事实，不提前透露输出。移除场景前，把仍需保留的条件移入题干。标题描述待判断的概念，不直接写出被考查的结论；每题须独立说明适用范围，不能依赖读者先看其他题。选项区分返回值、编译错误、异常和不返回的行为，只有真实字符串内容才用代码样式表示输出。

运行检查放在 `tests/Quiz.Checks/Types.cs`、`Execution.cs`、`Runtime.cs`；另有 `Foundations.cs`、`Modeling.cs`、`Queries.cs`；分别定义 `internal static class QuizTypes` / `QuizExecution` / `QuizRuntime` / `QuizFoundations` / `QuizModeling` / `QuizQueries`，提供 `internal static void Register(QuizSuite suite)`。用 `suite.Add("Q01", () => { ... })` 注册同步检查，或 `suite.AddAsync("Q21", async () => { ... })` 注册异步检查。共享断言为 `QuizAssert.Equal<T>(expected, actual)`、`QuizAssert.True(condition, message)`、`QuizAssert.Throws<TException>(Action)`、`await QuizAssert.ThrowsAsync<TException>(Func<Task>)`。问题片段可返回结果，断言放区域外；也可以使用 `QuizAssert.Capture(Action)` 取得标准输出（统一 LF，去掉末尾换行）。不依赖 GC 时机、线程编号、竞态碰巧发生或机器耗时；超时仅防止验证挂起。

故意不能编译的题放 `exercises/quiz/compile/Qxx.cs`，不加入正常项目；用完整、最小源码及 `#region`。验证字段为 `{"kind":"compile-error","path":"exercises/quiz/compile/Qxx.cs","diagnostics":["CSxxxx"],"note":"预期诊断及原因"}`。编译器将使用与仓库一致的配置，nullable 警告也会视作错误，必须说清楚语言错误还是仓库警告策略。

文档契约/工程判断题使用 `{"kind":"documentation","note":"人工逐项核对的契约及实验无法证明的边界"}`。来源必须在线实际核对，优先 Microsoft Learn / .NET 官方设计或固定版本源码。不要将有答案键、结构检查通过或一次运行冒称全部选项的自动语义证明。

`docs/quiz/` 中的七份题面、七份解析、七份 `*-lesson.md` 套题讲解、`coverage.md`、`knowledge-map.md` 和 `microsoft-map.md` 是生成文件；主入口、考试说明及研究复审记录由维护者编辑。运行 `python scripts/quiz.py render` 后提交生成页面；`python scripts/quiz.py check` 检查数据、摘录同步、答案证据与编译诊断。题号稳定，正文由数据生成，维护时修改 JSON / C# 后重新生成。

## 套题讲解

源数据在 `exercises/quiz/lessons/{types,execution,runtime,foundations,modeling,queries,microsoft}.json`。顶层字段为 `group`、`title`、`intro`、`sections`；每个主题含 `title`、`questions`、`code`、`result`、`explanation`（段落数组）和 `takeaway`。每组题目须各归属一次；microsoft 固定为 12 个单元、每单元连续 10 题，与报告分组一致。代码只引用该主题相关题目已有的源码区域；结果与契约边界仍须人工复审，不能只靠题号覆盖断言正确性。官方来源由相关题目汇总，避免另存一套链接。

围绕机制组织主题，按“代码或契约 → 观察结果 → 原因 → 工程判断”讲解，保留 C++ / Python 迁移的具体边界；不要只抄答案字母或把逐项解析拼成段落。讲解只在浏览器交卷后返回，新报告保存当时的讲解快照。讲解本身不参与试卷版本哈希，因此文字修订不会使当前作答失效；涉及题目、答案或源码的变化仍须按原题库版本规则处理。

## 浏览器考试

`python scripts/quiz.py exam` 读取同一份 JSON 与 C# 源码区域，可选迁移工程扩展卷 40 题、迁移专题单套 20 题或 Microsoft Learn 配套卷 120 题；不另建答案键或复制题面。配套卷的报告按 12 个学习单元分组。计分规则为每题 1 分，错答、漏答 0 分，百分制按实际试卷题数计算。

`scripts/quiz_exam.py` 负责本机服务、服务端评分和报告保存，`web/quiz/` 提供浏览器界面。交卷前的题面数据只含作答所需字段，不能暴露答案、解析或验证断言。修改题目、代码摘录、选项或答案后，须重新生成 Markdown 并重启考试服务；验收时同时检查旧草稿不会误套用到新题面。

考试报告写入 `artifacts/quiz-reports/`，该目录已被 Git 忽略；浏览器草稿与个人成绩不是课程源数据。维护验证不得改写 `learning/PROGRESS.md`、学习者答案或正式个人报告。完成修改后运行 `python scripts/verify.py` 和 `git diff --check`，并检查浏览器的作答、刷新恢复、交卷及报告下载；不要把源码检查当作浏览器验收。

`POST /api/lessons` 仅为同一题库版本的已交卷记录提供补充讲解：沿用提交令牌、作答编号、答案和用时校验，只读原报告。旧报告在浏览器中另存补充讲解，并单独下载 Markdown，不覆盖原报告文件或重算成绩。

页面只提供考试，`POST /api/practice` 已删除。`GET /api/exam` 只返回题面，交卷后报告默认展开全部题目的解析；回归须同时覆盖答对、错答和漏答题。多人服务复用同一评分器，按账号保存草稿与不可改写的报告；写入须校验会话、来源、CSRF、作答版本及修订号，重复保存 / 交卷不得重复计分。管理员汇总按试卷与完整版本分组，不将未交草稿算作成绩。

`practice-compatibility.json` 保留 2026-10-09 的精确措辞兼容审阅清单，属于历史证据。当前页面不再执行练习接续，浏览器中的原记录与备份按原始 JSON 只读下载，首次选择、统计和快照均不改写；不能把它们自动导入考试或重新评分。

维护时须覆盖全部历史练习存储键及备份的原始下载，不删除或覆盖其他卷的记录。个人浏览器记录、服务器账号数据库、备份、凭据、证书和下载文件不得提交 Git。题目变更仍须拒绝旧版本考试评分，旧报告保留交卷快照。

当前题库共 240 题：六组各 20 题的 Q01–Q120，以及独立 microsoft 组的 Q121–Q240。`scripts/quiz.py` 的 GROUPS / GROUP_RANGES 声明顺序和题号范围，COMBINED_GROUPS 限定完整迁移题池的原六组；扩展综合卷由 `migration-exam.json` 明确选择恰好 40 个原题号，按清单顺序和分组组织，支持规范的两位、三位编号；运行器按数字排序。microsoft 的运行检查在 `tests/Quiz.Checks/Microsoft.cs`，由 `QuizMicrosoft.Register` 注册。扩充需同步清单、注册、考试回归及文档，不能只追加 JSON。

迁移知识映射源在 `exercises/quiz/curriculum.json`，独立配套卷使用 `exercises/quiz/microsoft.curriculum.json`；每项含 title、questions、summary（段落数组）、learn。两份映射分别覆盖各自的 120 题，每题归属一次，检查器拒绝遗漏、重复或未知题号。归纳覆盖的是通用语言与工程主干，不冒称全站或所有框架全覆盖。

全仓验证包含考试的 Python 计分、报告持久化及本机 HTTP 回归。修改浏览器逻辑时，已安装 Node.js 18+ 的维护者还可在加载仓库环境后运行：

```sh
npm install --prefix .tools/ui-tests --no-save --package-lock=false --ignore-scripts jsdom@26.1.0
node --test tests/quiz_ui_checks.cjs tests/quiz_team_ui_checks.cjs
```

这组测试使用内存题库接口检查真实页面脚本的作答、恢复、交卷重试及报告下载，已接入三平台 CI；它不启动浏览器，不能代替视觉和浏览器兼容性验收。Node.js 与 jsdom 仅用于维护测试，启动考试仍只需仓库 Python。

## 40 题迁移工程扩展卷

`migration-exam.json` 维护标题、定位、分组重点与入选原题号；当前四组为 types 10、runtime 14、modeling 8、execution 8。检查器拒绝重复题号、跨组题号、Microsoft 题号和非 40 题总数。原七组题目 JSON、题号范围和证据保留，不另存答案键。专用讲解位于 `lessons/migration/{types,runtime,modeling,execution}.json`，每个入选题号恰好归属一个讲解主题，源码必须来自该主题关联的题目。生成 `docs/quiz/migration-exam.md` 与 `migration-lesson.md`，考试报告使用同一份专用讲解。

浏览器页面只列出扩展卷 40 题与 Microsoft Learn 120 题。扩展卷在展示层按选题顺序编号 Q01–Q40：`id` 仍是原题号，用于源码、提交、评分、草稿和历史报告；`display_id` 用于题面、答题卡、讲解链接与新报告，不进入作答版本哈希。不得直接改 JSON 或 C# 的原题号来整理页面编号，也不得按显示题号提交答案。旧报告没有 `display_id` 时使用其原号，保留原始快照。

`docs/quiz/question-bank.md` 是完整归档的单一阅读入口，由 `python scripts/quiz.py render` 生成。按扩展卷 40、微软卷 120、未入选迁移题 80 的顺序，每题仅出现一次，包含完整题面、源码、选项、答案、解释、验证命令及官方来源。锚点与验证命令使用原号，文件顶部提供扩展卷编号对照；归档保留在仓库文档中，浏览器首页不提供下载链接。分类题面和解析仍生成以保留已有文档引用，不能手改任何生成文件。

选题变化会改变综合卷版本，不可沿用仅限措辞修订的练习兼容清单。旧 120 题报告保留快照、旧草稿可导出、旧练习在重开前完整备份；不得自动截取作答或重算首次统计。其他单套与微软卷版本保持不变。回归须覆盖四组不同题数的计分、未入选题号拒绝、40 题讲解范围、旧 120 题报告/练习保留，以及单套和配套卷隔离。
