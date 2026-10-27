# 第 68 题 · Q68 · 异步释放的故障传播

原题号：`Q188`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

执行 await Q188()，得到的字符串是什么？

```csharp
private sealed class Resource188 : IAsyncDisposable
{
    public ValueTask DisposeAsync() => ValueTask.FromException(new InvalidOperationException("dispose failed"));
}

private static async Task<string> Q188()
{
    try
    {
        await using var resource = new Resource188();
    }
    catch (InvalidOperationException error) { return error.Message; }
    return "success";
}
```

- A. 编译失败。
- B. `body failed`
- C. `dispose failed`
- D. `success`
