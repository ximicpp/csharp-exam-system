# 08 · async / await

目标：掌握操作何时启动、如何等待失败或取消，以及 LINQ 重复枚举会怎样影响任务。

## 可运行入口

```sh
dotnet run --project samples/LanguageTour -- 08
```

## 调用启动操作，await 观察结果

[Program.cs](../samples/LanguageTour/Program.cs) 的 `Async()` 先启动两项操作，再一起等待；随后运行本章的两个边界实验。

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
static async Task Async()
{
    var first = FetchAsync(1);
    var second = FetchAsync(2);
    int[] results = await Task.WhenAll(first, second);
    Console.WriteLine($"results={string.Join(',', results)}");
    await AsyncBoundaries.CancelInFlightAsync();
    await AsyncBoundaries.EnumerateTasksAsync();
    static async Task<int> FetchAsync(int id)
    {
        Console.WriteLine($"start={id}");
        await Task.Delay(10); // 模拟等待；不根据耗时判断正确性。
        return id * 10;
    }
}
```

先输出（省略章节标题）：

```text
start=1
start=2
results=10,20
```

**普通 `async` 方法调用即执行**，直到遇到未完成的 `await` 才交回控制权；已完成的等待项可以同步继续。Python 的 `async def` 调用先创建 coroutine，通常要 await 或调度才执行函数体。

`Task<T>` 表示最终完成、失败或取消的操作；`await` 取得结果或传播异常。先 await 一个操作再调用下一个会串行；这里允许等待重叠。`WhenAll` 等全部结束，结果按输入顺序排列；它不会自动取消其他任务。多项失败时，返回任务保存全部异常，await 通常只抛其中一个。

## 取消：传入 token，发请求，再等待退出

以下方法位于 [AsyncBoundaries.cs](../samples/LanguageTour/AsyncBoundaries.cs)。先启动无限等待，保证取消发生在操作进行中，不依赖机器速度。

<!-- source: samples/LanguageTour/AsyncBoundaries.cs -->
```csharp
public static async Task CancelInFlightAsync()
{
    using var cancellation = new CancellationTokenSource();
    var pending = WaitAsync(cancellation.Token);
    Console.WriteLine($"cancel:completed={pending.IsCompleted}");
    cancellation.Cancel();
    try { await pending; }
    catch (OperationCanceledException) when (cancellation.IsCancellationRequested)
    {
        Console.WriteLine("cancel:observed");
    }
    Console.WriteLine($"cancel:canceled={pending.IsCanceled}");

    static async Task WaitAsync(CancellationToken token)
    {
        try { await Task.Delay(Timeout.Infinite, token); }
        finally { Console.WriteLine("cancel:cleanup"); }
    }
}
```

```text
cancel:completed=False
cancel:cleanup
cancel:observed
cancel:canceled=True
```

`Cancel()` 发合作式请求；`WaitAsync` 把 token 传给 `Task.Delay`，取消异常经 `finally` 清理后继续向调用方传播。**Cancel 返回不等于操作已退出，仍应 await pending。** 自己的 CPU 循环需定期调用 `token.ThrowIfCancellationRequested()`；不读取 token 的代码不会被强行终止。`using` 最后释放 Source，释放本身不发送取消请求。[取消模型](https://learn.microsoft.com/en-us/dotnet/standard/threading/cancellation-in-managed-threads)

## LINQ 查询不是已经创建好的 Task 数组

同文件用调用计数演示重复启动；`Task.FromResult` 返回已完成的 Task，无需计时或真实网络请求。

<!-- source: samples/LanguageTour/AsyncBoundaries.cs -->
```csharp
public static async Task EnumerateTasksAsync()
{
    int starts = 0;
    Task<int> Start(int id)
    {
        starts++;
        return Task.FromResult(id * 10);
    }
    IEnumerable<Task<int>> query = new[] { 1, 2 }.Select(Start);
    Console.WriteLine($"starts:deferred={starts}");
    await Task.WhenAll(query);
    Console.WriteLine($"starts:first={starts}");
    await Task.WhenAll(query);
    Console.WriteLine($"starts:second={starts}");

    Task<int>[] tasks = query.ToArray();
    await Task.WhenAll(tasks);
    await Task.WhenAll(tasks);
    Console.WriteLine($"starts:array-twice={starts}");
}
```

```text
starts:deferred=0
starts:first=2
starts:second=4
starts:array-twice=6
```

`Select` 只创建查询，每次 `WhenAll(query)` 枚举时才调用 `Start`；换成 HTTP 或写入 API 就可能重复请求。`ToArray()` 又启动一批，计数从 4 到 6，之后两次等待数组都复用同一组 Task，不重新调用 `Start`。需要复用时，在创建查询后立即物化一次，再传递数组。[Select](https://learn.microsoft.com/en-us/dotnet/api/system.linq.enumerable.select?view=net-10.0) · [WhenAll](https://learn.microsoft.com/en-us/dotnet/api/system.threading.tasks.task.whenall?view=net-10.0)

## 迁移误区

- Task 不保证有专属线程，await 不保证换线程。I/O 使用异步 API；CPU 计算才考虑 `Task.Run`。
- `.Result` / `.Wait()` 阻塞线程，在某些同步上下文会死锁。
- 除事件处理器外，使用 `Task` 返回类型；`async void` 让调用者难以等待和接收异常。
- `WhenAll` 没有并发上限；大量请求需限流，物化任务也不解决并发上限。

## 练习与验收

任选一种练习方式：[在线引导题 08](online.md) 自动检查批量调用的启动顺序、结果顺序与取消；或按下面的步骤修改本章示例。

可选练习：修改 [Program.cs](../samples/LanguageTour/Program.cs) 的 `Async()`：

1. 在 `FetchAsync` 的 `await Task.Delay(10)` 后，仅当 `id == 1` 时抛出 `new InvalidOperationException("fetch=1")`。
2. 用 `try/catch (InvalidOperationException error)` 包住现有 `await Task.WhenAll(first, second)` 和 `results` 输出；catch 打印 `caught={error.Message}`。
3. 在该 try/catch 后打印 `second={second.Status}; result={await second}`，保留后面的两个 `AsyncBoundaries` 调用。

从仓库根目录运行 `dotnet run --project samples/LanguageTour -- 08`。

验收：退出码为 0；除章节标题外，依次输出以下内容，不出现 `results=` 或未处理异常：

```text
start=1
start=2
caught=fetch=1
second=RanToCompletion; result=20
cancel:completed=False
cancel:cleanup
cancel:observed
cancel:canceled=True
starts:deferred=0
starts:first=2
starts:second=4
starts:array-twice=6
```

主线下一站：[实战 LogLens](11-project.md)。按需查阅：[工程与验证](09-engineering.md) · [异步状态机](14-execution-model.md)。
