# 第 82 题 · Q82 · WhenAny 与获胜任务的异常

原题号：`Q202`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

执行 await Q202()，得到的字符串是什么？

```csharp
private static async Task<string> Q202()
{
    Task<int> failed = Task.FromException<int>(new InvalidOperationException("failed"));
    var pending = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
    Task<int> winner = await Task.WhenAny(failed, pending.Task);
    try { _ = await winner; }
    catch (InvalidOperationException) { pending.SetResult(0); return $"{ReferenceEquals(winner, failed)},{winner.IsFaulted}"; }
    return "success";
}
```

- A. `False,True`
- B. `True,True`
- C. `success`
- D. `True,False`
