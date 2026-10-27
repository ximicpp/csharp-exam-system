# 第 65 题 · Q65 · 异常过滤器与后续 catch

原题号：`Q185`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q185()，返回的字符串是什么？

```csharp
private static string Q185()
{
    List<string> log = [];
    bool Accept() { log.Add("filter"); return false; }
    try { throw new InvalidOperationException(); }
    catch (InvalidOperationException) when (Accept()) { log.Add("first"); }
    catch (InvalidOperationException) { log.Add("fallback"); }
    return string.Join(",", log);
}
```

- A. `filter,fallback`
- B. `filter,first`
- C. `fallback`
- D. `filter,first,fallback`
