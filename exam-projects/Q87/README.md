# 第 87 题 · Q87 · await foreach 提前退出的收尾

原题号：`Q207`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

执行 await Q207()，得到的字符串是什么？

```csharp
private static async IAsyncEnumerable<int> Read207(List<string> log)
{
    try
    {
        yield return 1;
        await Task.CompletedTask;
        yield return 2;
    }
    finally { log.Add("close"); }
}

private static async Task<string> Q207()
{
    List<string> log = [];
    await foreach (int value in Read207(log)) { log.Add($"item{value}"); break; }
    return string.Join(",", log);
}
```

- A. `item1`
- B. `item1,item2,close`
- C. `close,item1`
- D. `item1,close`
