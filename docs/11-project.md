# 11 · 实战：LogLens

目标：用一个流式日志分析器串联类型、资源所有权、LINQ 和异步。

## 可运行入口

```sh
dotnet run --project src/LogLens.Cli -- data/requests.jsonl
python scripts/verify.py
```

输入是[合成 JSON Lines](../data/requests.jsonl)。先按“输入模型 → 校验 → 累积 → 输出”阅读 [Analyzer.cs](../src/LogLens/Analyzer.cs) 的关键代码，再看 CLI 如何调用它；片段来自仓库中的可编译项目。

## 用 record 定义边界

<!-- source: src/LogLens/Analyzer.cs -->
```csharp
public sealed record RequestEntry(string Path, int Status, double DurationMs);
public sealed record PathSummary(string Path, long Count, long Errors, double AverageMs);
public sealed record AnalysisResult(long Valid, long Invalid, IReadOnlyList<PathSummary> Paths);
```

单行输入转换为 `RequestEntry`；每个路径只输出一个 `PathSummary`。位置式 record 为参数生成属性，并提供值相等性，见[类型与建模](03-modeling.md)。CLI 序列化 `AnalysisResult`，属性名直接出现在 JSON 中。第一条命令输出以下结果（空白不影响结果），退出码为 0：

```text
{
  "Valid": 4,
  "Invalid": 2,
  "Paths": [
    { "Path": "/api/users", "Count": 3, "Errors": 1, "AverageMs": 20 },
    { "Path": "/health", "Count": 1, "Errors": 0, "AverageMs": 2 }
  ]
}
```

## TryParse：在入口拒绝坏数据

这是 `Analyzer` 中完整的 `TryParse` 方法；JSON API 来自文件顶部导入的 `System.Text.Json`：

<!-- source: src/LogLens/Analyzer.cs -->
```csharp
public static bool TryParse(string line, out RequestEntry? entry)
{
    entry = null;
    try
    {
        using var document = JsonDocument.Parse(line);
        var root = document.RootElement;
        if (root.ValueKind != JsonValueKind.Object ||
            !TryReadFields(root, out string? route, out int code, out double ms) ||
            string.IsNullOrWhiteSpace(route) || code is < 100 or > 599 ||
            !double.IsFinite(ms) || ms < 0)
            return false;
        entry = new RequestEntry(route, code, ms);
        return true;
    }
    catch (JsonException) { return false; }
    catch (ArgumentException error) when (error.InnerException is System.Text.EncoderFallbackException)
    {
        return false;
    }
}
```

先把 `out` 参数设为 null，保证失败返回前也已赋值。599 合法、600 非法，耗时必须有限且非负；`using` 释放解析文档，返回的 record 保存取出的字符串和数值。

字段读取单独放在下面的辅助方法中。JSON 文档能解析，不代表所有字符串已解码：孤立的 `\uD800` / `\uDC00` 可在读取时失败，字段名反转义也可能失败。只在 DOM 读取边界接收这类 `InvalidOperationException`，业务校验和对象构造不被该 catch 包住：

<!-- source: src/LogLens/Analyzer.cs -->
```csharp
private static bool TryReadFields(JsonElement root, out string? route, out int code, out double ms)
{
    route = null;
    code = 0;
    ms = 0;
    try
    {
        if (!root.TryGetProperty("path", out var path) || path.ValueKind != JsonValueKind.String ||
            !root.TryGetProperty("status", out var status) || status.ValueKind != JsonValueKind.Number ||
            !status.TryGetInt32(out code) ||
            !root.TryGetProperty("durationMs", out var duration) || duration.ValueKind != JsonValueKind.Number ||
            !duration.TryGetDouble(out ms))
            return false;
        route = path.GetString();
        return true;
    }
    // DOM 字段名和字符串的反转义仍可能因无效 UTF-16 抛出此异常。
    catch (InvalidOperationException) { return false; }
}
```

例如 `{"path":"\uD800","status":200,"durationMs":1}` 返回 false，后续正常行继续处理；合法代理对 `\uD83D\uDE00` 能正常解码。解析语法错误由外层 `JsonException` 处理；若传入的 .NET 字符串本身含孤立代理项，则由带编码异常过滤器的 catch 处理，其他参数错误仍向外传播。

## AnalyzeAsync：逐行读取、按路径累积

`AnalyzeAsync(TextReader reader, CancellationToken cancellationToken = default)` 的读取循环：

<!-- source: src/LogLens/Analyzer.cs -->
```csharp
long valid = 0, invalid = 0;
var groups = new Dictionary<string, Accumulator>(StringComparer.Ordinal);
// reader 由调用方拥有，本方法只读取，不负责关闭。
while (true)
{
    cancellationToken.ThrowIfCancellationRequested();
    string? line = await reader.ReadLineAsync(cancellationToken);
    if (line is null) break;
    if (!TryParse(line, out var entry) || entry is null)
    {
        invalid++;
        continue;
    }
    valid++;
    if (!groups.TryGetValue(entry.Path, out var group))
    {
        group = new Accumulator();
        groups.Add(entry.Path, group);
    }
    group.Add(entry);
}
```

`null` 是 EOF，空字符串是一条坏行。只有通过解析的条目才进入 `Add`；取消异常直接向调用者传播，不增加 Invalid。

每个路径的聚合状态由嵌套类型 `Accumulator` 保存：

<!-- source: src/LogLens/Analyzer.cs -->
```csharp
private sealed class Accumulator
{
    public long Count { get; private set; }
    public long Errors { get; private set; }
    public double Mean { get; private set; }
    public void Add(RequestEntry entry)
    {
        Count++;
        if (entry.Status >= 500) Errors++;
        // 在线均值，不保留全部行，也不对极大耗时直接求和。
        Mean += (entry.DurationMs - Mean) / Count;
    }
}
```

例如 30、10 两次耗时使 `Mean` 从 0 变为 30，再变为 20。循环结束后，`AnalyzeAsync` 才把字典排序、投影为输出数组：

<!-- source: src/LogLens/Analyzer.cs -->
```csharp
cancellationToken.ThrowIfCancellationRequested();
var paths = groups.OrderBy(pair => pair.Key, StringComparer.Ordinal)
    .Select(pair => new PathSummary(pair.Key, pair.Value.Count,
        pair.Value.Errors, pair.Value.Mean)).ToArray();
return new AnalysisResult(valid, invalid, paths);
```

## 契约

- 字段名区分大小写；路径非空白，状态码是 100–599 的整数，耗时有限且非负。
- 坏 JSON、字段读取时的 Unicode 解码失败、缺字段、类型错误及空行计入 Invalid 后继续；多余字段不参与聚合。
- 路径按 Ordinal 分组、排序；Errors 仅计 5xx，404 是有效请求。
- 空文件输出零计数和空数组；成功返回 0，读取失败返回 1，参数数量错误返回 2，取消返回 130。错误写 stderr。

## CLI：把资源、取消和错误边界接起来

[CLI](../src/LogLens.Cli/Program.cs) 完成参数检查后执行以下代码：

<!-- source: src/LogLens.Cli/Program.cs -->
```csharp
using var cancellation = new CancellationTokenSource();
ConsoleCancelEventHandler handler = (_, e) => { e.Cancel = true; cancellation.Cancel(); };
Console.CancelKeyPress += handler;
try
{
    using var reader = new StreamReader(args[0]);
    var result = await Analyzer.AnalyzeAsync(reader, cancellation.Token);
    Console.WriteLine(JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
    return 0;
}
catch (OperationCanceledException)
{
    Console.Error.WriteLine("Cancelled.");
    return 130;
}
catch (Exception error) when (error is IOException or UnauthorizedAccessException or ArgumentException)
{
    Console.Error.WriteLine($"Cannot read input: {error.Message}");
    return 1;
}
finally { Console.CancelKeyPress -= handler; }
```

CLI 创建并拥有 reader 与取消源，`using` 让成功、失败和提前返回都经过释放；Analyzer 只借用 reader，token 逐层传给读取操作。

Ctrl+C 回调将 `e.Cancel` 设为 true，阻止默认终止并发出合作式取消；异常到达 CLI 后转换为退出码，`catch ... when` 只接收列出的输入错误，其余异常继续传播。

`finally` 解除静态事件的订阅，避免处理器在退出这段逻辑后继续被保留或调用；[行为检查](../tests/Course.Checks/Program.cs)与[统一验证](../scripts/verify.py)覆盖库行为和 CLI 契约。

## 迁移误区

- `ReadAllLines + GroupBy` 保存全部输入；此实现只保留当前行与 K 个路径的聚合状态，内存仍受路径数和单行长度影响。
- 异步读取不等于并行操作同一个 reader；取消也不能记成坏行。

## 练习与验收

可选练习：修改 [Analyzer.cs](../src/LogLens/Analyzer.cs)，为 `PathSummary` 增加 `double MaxMs`；在 `Accumulator.Add` 内按路径更新最大耗时，生成 `PathSummary` 时传入该值。继续逐行处理，不保存所有请求；CLI 会自动序列化新增属性。

验收输入已入库：[exercise-11.jsonl](../data/exercise-11.jsonl) 包含两个路径、零耗时、599、600 和坏 JSON；[empty.jsonl](../data/empty.jsonl) 为 0 字节。先完成修改，再从仓库根目录运行：

```sh
dotnet run --project src/LogLens.Cli -- data/exercise-11.jsonl
dotnet run --project src/LogLens.Cli -- data/empty.jsonl
```

验收：两次退出码均为 0。第一份 JSON 的 `Valid=4`、`Invalid=2`，`Paths` 按以下顺序输出（JSON 空白不影响验收）：

| Path | Count | Errors | AverageMs | MaxMs |
| --- | --- | --- | --- | --- |
| /a | 2 | 1 | 20 | 30 |
| /b | 2 | 0 | 2 | 4 |

状态码 600 的行有耗时 9999，但不能进入计数、均值或最大值。第二份 JSON 必须为 `{"Valid":0,"Invalid":0,"Paths":[]}`，不能生成占位分组。未完成练习时第一份输出没有 `MaxMs`，这是待实现部分。

本题改变 CLI 的 JSON 契约，课程基线检查仍期待原字段；先按以上命令验收，正式合入时再同步基线预期。发布方式见[第 09 章](09-engineering.md)。
