# 第 58 题 · Q58 · 多播调用遇到异常

原题号：`Q178`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q178()，返回的字符串是什么？

```csharp
private static string Q178()
{
    List<string> log = [];
    Action handlers = () => log.Add("first");
    handlers += () => throw new InvalidOperationException("broken");
    handlers += () => log.Add("last");
    try { handlers(); }
    catch (InvalidOperationException) { log.Add("caught"); }
    return string.Join(",", log);
}
```

- A. `first,caught`
- B. `first,last,caught`
- C. `first,last`
- D. `caught`
