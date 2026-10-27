# 第 83 题 · Q83 · WhenAll 的结果顺序

原题号：`Q203`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

执行 await Q203()，得到的字符串是什么？

```csharp
private static async Task<string> Q203()
{
    var first = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
    var second = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
    Task<int[]> combined = Task.WhenAll(first.Task, second.Task);
    second.SetResult(20);
    first.SetResult(10);
    return string.Join(",", await combined);
}
```

- A. 编译失败。
- B. `10,20`
- C. `20,10`
- D. `10`
