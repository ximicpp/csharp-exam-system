# 09 · 工程与验证

目标：读懂项目依赖，构建并发布命令行工具。

## 可运行入口

```sh
python scripts/verify.py
dotnet publish src/LogLens.Cli -c Release --no-self-contained -o artifacts/loglens
dotnet artifacts/loglens/LogLens.Cli.dll data/requests.jsonl
```

## 项目如何依赖库

[src/LogLens.Cli/LogLens.Cli.csproj](../src/LogLens.Cli/LogLens.Cli.csproj) 是 CLI 的完整项目文件：

<!-- source: src/LogLens.Cli/LogLens.Cli.csproj -->
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
  </PropertyGroup>
  <ItemGroup>
    <ProjectReference Include="../LogLens/LogLens.csproj" />
  </ItemGroup>
</Project>
```

`ProjectReference` 声明 `LogLens.Cli → LogLens`；路径相对于这个 csproj。`Course.Checks` 同样引用库，LanguageTour、RuntimeLab 独立。目标框架、可空检查等共同配置由 [Directory.Build.props](../Directory.Build.props) 提供，[解决方案](../CSharpCourse.slnx)聚合项目。

| 依赖声明 | 指向什么 | 构建时如何取得 |
| --- | --- | --- |
| `ProjectReference` | 另一个 `.csproj` | 构建被引用项目，使用其输出 |
| `PackageReference` | NuGet 包名及版本 | 还原包及其依赖，使用包中的程序集等资产 |

本课没有第三方包；普通项目使用 `PackageReference` 声明包依赖，NuGet 负责解析和下载。包缓存在本机，不把包文件复制进源码目录；`using` 只简化类型名，不安装或引用包。[包引用](https://learn.microsoft.com/en-us/nuget/consume-packages/package-references-in-project-files)

## restore、build、publish 各做什么

| 命令（仓库根目录） | 结果 |
| --- | --- |
| `dotnet restore CSharpCourse.slnx` | 解析依赖，下载缺少的包并生成 `obj/project.assets.json` 等还原信息 |
| `dotnet build CSharpCourse.slnx -c Release` | 编译解决方案中的项目及依赖，生成 `bin/Release` 下的产物 |
| 上方 `dotnet publish` | 构建 CLI，并把运行所需文件收集到 `artifacts/loglens` |

`build` / `run` / `publish` 默认隐式 restore；只想正常构建时不必先手动执行一遍。需要在 CI 中分开还原和构建时，可先 restore，再给后续命令加 `--no-restore`。[restore](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-restore) · [build](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-build)

本例是框架依赖部署：目标机器仍需 .NET 10 Runtime。分发整个发布目录，其中包括 CLI、LogLens 库和运行配置；不能只拿走一个 DLL。自包含发布则把 Runtime 一起带上，需要选择目标 RID。[publish](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-publish)

## 行为检查就是调用与断言

[tests/Course.Checks/Program.cs](../tests/Course.Checks/Program.cs) 在顶层定义一个检查函数，失败抛异常，使进程返回非零：

<!-- source: tests/Course.Checks/Program.cs -->
```csharp
int checks = 0;
void Check(bool condition, string message)
{
    if (!condition) throw new InvalidOperationException(message);
    checks++;
}
```

同一文件用内存 reader 输入四行，直接调用生产代码，检查计数、排序、5xx 与均值：

<!-- source: tests/Course.Checks/Program.cs -->
```csharp
using var input = new StringReader("""
{"path":"/z","status":500,"durationMs":30}
bad
{"path":"/a","status":404,"durationMs":2}
{"path":"/z","status":200,"durationMs":10}
""");
var result = await Analyzer.AnalyzeAsync(input);
Check(result.Valid == 3 && result.Invalid == 1, "valid/invalid counts");
Check(result.Paths.Count == 2 && result.Paths[0].Path == "/a", "ordinal ordering");
Check(result.Paths[0].Errors == 0 && result.Paths[1].Errors == 1, "only 5xx are errors");
Check(result.Paths[1].Count == 2 && result.Paths[1].AverageMs == 20, "group average");
```

这些片段摘自完整检查程序；从仓库根目录单独运行：

```sh
dotnet run --project tests/Course.Checks -c Release
```

成功输出 `PASS: 29 behavior checks`。`python scripts/verify.py` 还检查 Release 构建、示例输出、分配对照、CLI 契约、发布产物和文档，成功以 `PASS: repository verification` 结束。Windows / Linux / macOS CI 从干净环境运行 [setup](setup.md)，再检查重复执行及新终端激活。

## 选择题库维护

[60 道选择题](quiz/index.md)的数据保存在 `exercises/quiz/`，运行证据位于 `tests/Quiz.Checks/`，故意不能编译的源码单独保存在 `exercises/quiz/compile/`。修改题目数据或源码区域后，在根目录执行：

```sh
python scripts/quiz.py render
python scripts/verify.py
git diff --check
```

`render` 生成分开的题面、逐项解析与覆盖索引；不要直接修改生成页。全仓验证包含选择题的数据结构、源码摘录、页面同步、运行断言与负向编译诊断。仅检查题库可运行 `python scripts/quiz.py check`，单题证据可加 `--id Q03`。编译诊断题先验证合法对照，随后要求编译失败且诊断集合吻合；官方契约题仍需人工核对来源和所有选项，不把结构检查称作自动证明答案。审核取舍与迭代结果记在[题库复审](quiz/review.md)。

## 迁移误区

当前考试的 160 个独立项目另见[每题一个项目](exam-projects.md)。`python scripts/exam_projects.py check --id Q124` 验收单题；省略 `--id` 验收全部。全仓验证同时构建 `exam/CSharpExam.slnx` 的 Release 产物、运行每题断言并验证 11 个编译负例，原课程仍使用自己的解决方案。

- Course.Checks 是控制台检查程序，验收入口是 `verify.py`，不是 `dotnet test`。
- 接入已有项目时沿用团队的测试框架与运行器；本课的断言可迁移，不必为学习增加依赖。
- `dotnet run` 面向项目；发布后的 DLL 可直接交给 `dotnet` 运行。
- `bin/`、`obj/`、`artifacts/` 可重建，不提交。

## 练习与验收

可选练习：不修改源码，发布 [LogLens.Cli](../src/LogLens.Cli/LogLens.Cli.csproj)，直接运行发布产物。先加载环境，再从仓库根目录依次执行；第一条命令会创建输出目录：

```sh
dotnet publish src/LogLens.Cli -c Release --no-self-contained -o artifacts/loglens
dotnet artifacts/loglens/LogLens.Cli.dll data/requests.jsonl
dotnet artifacts/loglens/LogLens.Cli.dll data/empty.jsonl
dotnet artifacts/loglens/LogLens.Cli.dll
```

验收（JSON 空白不影响结果）：

- 发布退出码为 0。第一份输入退出码为 0，输出 `Valid=4`、`Invalid=2`；`Paths` 依次为 `/api/users`（Count=3、Errors=1、AverageMs=20）和 `/health`（Count=1、Errors=0、AverageMs=2）。
- 空文件退出码为 0，输出 `{"Valid":0,"Invalid":0,"Paths":[]}`。
- 无参数运行退出码为 2，stdout 为空，stderr 输出 `Usage: LogLens.Cli <requests.jsonl>`。

退出码需在每条命令后检查：PowerShell 查看 `$LASTEXITCODE`，Bash 查看 `$?`。输入和发布配置均在仓库内，不需要 IDE 或手工复制依赖。CLI 如何实现这些边界见[第 11 章](11-project.md)。

下一章：[性能](10-performance.md)。
