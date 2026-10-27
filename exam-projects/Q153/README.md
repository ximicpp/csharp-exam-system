# 第 153 题 · Q153 · await using 的完成边界与所有权

原题号：`Q22`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

方法已接管连接的释放责任，调用方要等连接完全关闭后再结束服务。

在所示 UseOwnedAsync 契约下，调用方观察到哪个时点，才能确定 lease 的异步清理已成功完成？

```csharp
private sealed class AsyncLease(Task finishDispose) : IAsyncDisposable
{
    public TaskCompletionSource DisposeStarted { get; } =
        new(TaskCreationOptions.RunContinuationsAsynchronously);
    public bool Disposed { get; private set; }

    public async ValueTask DisposeAsync()
    {
        DisposeStarted.SetResult();
        await finishDispose;
        Disposed = true;
    }
}

// 此方法的契约是接管 lease 的释放责任。
private static async Task UseOwnedAsync(AsyncLease lease)
{
    await using (lease)
    {
        await Task.CompletedTask;
    }
}

private static async Task<(bool, bool)> Q22()
{
    var finish = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
    var lease = new AsyncLease(finish.Task);
    Task operation = UseOwnedAsync(lease);
    await lease.DisposeStarted.Task;
    bool pending = !operation.IsCompleted;
    finish.SetResult();
    await operation;
    return (pending, lease.Disposed);
}
```

- A. UseOwnedAsync 已返回 operation 这个 Task 对象。
- B. lease.DisposeStarted.Task 已成功完成。
- C. await operation 已成功结束。
- D. finish.SetResult() 已返回。
