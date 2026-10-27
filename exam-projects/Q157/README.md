# 第 157 题 · Q157 · 取消请求与清理完成

原题号：`Q35`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

宿主请求取消导出后，要确认导出任务的 finally 已执行完，才能宣布该操作停止。

Q35 用信号分别控制观察取消、进入清理和完成清理。哪个观察结果足以确认 WorkAsync 的 finally 已经结束？

```csharp
private static async Task<(bool AfterCancel, bool DuringCleanup, bool Cleaned, bool Canceled)> Q35()
{
    using var cts = new CancellationTokenSource();
    var observe = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
    var cleaning = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
    var finish = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
    bool cleaned = false;
    async Task WorkAsync()
    {
        try
        {
            await observe.Task;
            cts.Token.ThrowIfCancellationRequested();
        }
        finally
        {
            cleaning.SetResult();
            await finish.Task;
            cleaned = true;
        }
    }
    Task work = WorkAsync();
    cts.Cancel();
    bool afterCancel = !work.IsCompleted;
    observe.SetResult();
    await cleaning.Task;
    bool duringCleanup = !work.IsCompleted;
    finish.SetResult();
    try { await work; }
    catch (OperationCanceledException) when (cts.IsCancellationRequested) { }
    return (afterCancel, duringCleanup, cleaned, work.IsCanceled);
}
```

- A. cts.Cancel() 已返回。
- B. await cleaning.Task 已结束。
- C. await work 已抛出并由外层 catch 观察到 OperationCanceledException。
- D. finish.SetResult() 已返回。
