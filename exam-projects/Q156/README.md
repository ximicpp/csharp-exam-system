# 第 156 题 · Q156 · WhenAll 的故障完成与异常观察

原题号：`Q34`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

并发批次中的两个操作都失败，故障报告必须包含两项错误，而不只记录 await 抛出的那一项。

若要在 Q34 的 catch 中取得两个操作的全部原始异常，应采用哪种做法？不依赖 await 选择哪一个异常。

```csharp
private static async Task<(bool Pending, int Failures, bool OneOriginal)> Q34()
{
    var second = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
    var firstError = new InvalidOperationException("first");
    var secondError = new ArgumentException("second");
    Task all = Task.WhenAll(Task.FromException(firstError), second.Task);
    bool pending = !all.IsCompleted;
    second.SetException(secondError);
    Exception? observed = null;
    try { await all; }
    catch (Exception error) { observed = error; }
    return (pending, all.Exception!.InnerExceptions.Count,
        ReferenceEquals(observed, firstError) || ReferenceEquals(observed, secondError));
}
```

- A. 读取 all.Exception!.InnerExceptions。
- B. 将 catch 捕获的 error 强制转换为 AggregateException，再读取 InnerExceptions。
- C. 再 await all 一次，收集这次抛出的另一个异常。
- D. 只读取 second.Task.Exception!.InnerExceptions。

## 动手问题

- 比较 await 捕获的异常与任务保存的异常集合；当其中一个错误本身是 AggregateException 时，观察到的信息有哪些变化？
