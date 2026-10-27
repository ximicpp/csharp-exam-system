# 第 90 题 · Q90 · WaitAsync 的取消边界

原题号：`Q210`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

执行 await Q210()，得到的字符串是什么？

```csharp
private static async Task<string> Q210()
{
    var work = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
    CancellationToken token = new(canceled: true);
    try { _ = await work.Task.WaitAsync(token); }
    catch (OperationCanceledException)
    {
        bool originalCompleted = work.Task.IsCompleted;
        work.SetResult(7);
        return $"{originalCompleted},{await work.Task}";
    }
    return "unexpected";
}
```

- A. `True,7`
- B. `True,canceled`
- C. `unexpected`
- D. `False,7`
