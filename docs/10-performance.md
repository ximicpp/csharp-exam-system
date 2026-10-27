# 10 · 性能边界

目标：识别分配与装箱，在保持结果正确的前提下测量一次优化。

## 可运行入口

```sh
dotnet run --project samples/LanguageTour -c Release -- 10
```

## 视图与装箱

[Program.cs](../samples/LanguageTour/Program.cs) 的 `Performance()` 先演示字符串切片与装箱复制：

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
string text = "latency=125";
ReadOnlySpan<char> digits = text.AsSpan("latency=".Length);
Console.WriteLine($"latency={int.Parse(digits, CultureInfo.InvariantCulture)}");
int value = 42;
object boxed = value;
value = 7;
Console.WriteLine($"value={value}; boxed={(int)boxed}");
```

除章节标题外，前两行输出：

```text
latency=125
value=7; boxed=42
```

`digits` 是原字符串中 `125` 的视图，`int.Parse` 直接读取它；`AsSpan` 不创建子字符串，但不保证整个函数零分配。`object boxed = value` 则把 42 的副本装箱；之后改 `value`，箱中仍是 42，`(int)boxed` 解箱取得该值。

**Span 是连续内存的视图，不拥有底层数据。** `Span<T>` 也可引用数组或栈内存，并不等于“栈数组”。它和 `ReadOnlySpan<T>` 都是 `ref struct`：不能作为普通 class 的字段，也不能跨 await 挂起点存活。跨异步边界保存视图可考虑 `Memory<T>` / `ReadOnlyMemory<T>`，仍需明确底层内存的所有权。

## 测量：相同解析结果，不同临时分配

随后调用 [AllocationLesson.Run()](../samples/LanguageTour/AllocationLesson.cs)。两个实现解析同一个 `latency=125`；本文件引入 `System.Globalization` 和 `System.Runtime.CompilerServices`：

<!-- source: samples/LanguageTour/AllocationLesson.cs -->
```csharp
private static int ParseWithSubstring(string text) =>
    ParseString(text.Substring("latency=".Length));

private static int ParseWithSpan(string text) =>
    int.Parse(text.AsSpan("latency=".Length), CultureInfo.InvariantCulture);

// Keep the substring as a string across a call boundary for this allocation experiment.
[MethodImpl(MethodImplOptions.NoInlining)]
private static int ParseString(string digits) =>
    int.Parse(digits, CultureInfo.InvariantCulture);
```

`Substring` 在这里创建非空子字符串，`AsSpan` 提供原字符串的视图。`NoInlining` 让接收字符串的辅助方法保留调用边界，避免实验只测到内联优化后的另一种路径；它是测量辅助，不是业务优化建议。

计数器给出**当前线程累计分配的托管字节数**，前后相减才是本段分配；它不是当前存活内存、内存峰值或耗时，也不计其他线程和原生分配。测量区内不输出、不 `await`；返回校验和，避免丢弃解析结果：

<!-- source: samples/LanguageTour/AllocationLesson.cs -->
```csharp
private static (long Bytes, int Sum) Measure(Func<string, int> parse, string input, int iterations)
{
    int sum = 0;
    long before = GC.GetAllocatedBytesForCurrentThread();
    for (int i = 0; i < iterations; i++) sum += parse(input);
    long bytes = GC.GetAllocatedBytesForCurrentThread() - before;
    return (bytes, sum);
}
```

先预热，再分别重复 10,000 次；委托传入后才开始计数。所有输出都在测量结束后：

<!-- source: samples/LanguageTour/AllocationLesson.cs -->
```csharp
public static void Run()
{
    const string input = "latency=125";
    const int iterations = 10_000;
    _ = Measure(ParseWithSubstring, input, iterations);
    _ = Measure(ParseWithSpan, input, iterations);

    var substring = Measure(ParseWithSubstring, input, iterations);
    var span = Measure(ParseWithSpan, input, iterations);
    Console.WriteLine($"allocation:substring-bytes={substring.Bytes}");
    Console.WriteLine($"allocation:span-bytes={span.Bytes}");
    Console.WriteLine($"allocation:equal={substring.Sum == span.Sum}; checksum={span.Sum}");
}
```

接下来的两行 `allocation:substring-bytes=...`、`allocation:span-bytes=...` 给出实测整数；本实验应观察到前者更大。最后一行为 `allocation:equal=True; checksum=1250000`，证明两条路径的解析结果一致。具体字节数随运行时和平台而变，不以固定数值或速度比例验收。[计数器语义](https://learn.microsoft.com/en-us/dotnet/api/system.gc.getallocatedbytesforcurrentthread?view=net-10.0)。

## 迁移误区

- 将 class 改成 struct 可能引入大值复制，不能据此断言更快。
- GC 仍有成本。热路径检查子字符串、闭包、装箱、临时集合及 LINQ 重复枚举。
- LogLens 的聚合项随不同路径数 K 增长，另需容纳当前行；流式读取不保证常量内存。
- 保留正确性检查，用 Release、预热和多次测量区分 JIT、初始化等成本；微基准可用 BenchmarkDotNet。

## 练习与验收

可选练习：先运行本章命令，记录 `allocation:substring-bytes` 的基线值。只修改 [AllocationLesson.cs](../samples/LanguageTour/AllocationLesson.cs) 的 `ParseWithSubstring`：把创建子字符串再调用 `ParseString`，改为直接使用 `AsSpan` 和 `int.Parse`；保留方法名、预热、循环次数和其余代码。

从仓库根目录重新运行 `dotnet run --project samples/LanguageTour -c Release -- 10`。

验收：修改前后退出码均为 0；`latency=125`、`value=7; boxed=42` 和 `allocation:equal=True; checksum=1250000` 不变；修改后的 `allocation:substring-bytes` 小于自己记录的基线值。输出标签保留旧实现名便于对照，不要求两个实测数精确相等或为 0。若分配没有下降，检查是否仍先调用了 `Substring`，再转为 Span。

下一章：[实战：LogLens](11-project.md)。
