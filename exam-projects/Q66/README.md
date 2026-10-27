# 第 66 题 · Q66 · using 声明的释放边界

原题号：`Q186`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q186()，返回的字符串是什么？

```csharp
private sealed class Resource186(List<string> log) : IDisposable
{
    public void Dispose() => log.Add("dispose");
}

private static string Q186()
{
    List<string> log = [];
    {
        using var resource = new Resource186(log);
        log.Add("body");
        log.Add("tail");
    }
    log.Add("outer");
    return string.Join(",", log);
}
```

- A. `dispose,body,tail,outer`
- B. `body,dispose,tail,outer`
- C. `body,tail,outer,dispose`
- D. `body,tail,dispose,outer`
