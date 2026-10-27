# 第 61 题 · Q61 · catch 与 finally 的执行顺序

原题号：`Q181`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q181()，返回的字符串是什么？

```csharp
private static string Q181()
{
    List<string> log = [];
    try { log.Add("try"); throw new FormatException(); }
    catch (FormatException) { log.Add("catch"); }
    finally { log.Add("finally"); }
    log.Add("after");
    return string.Join(",", log);
}
```

- A. `try,finally,after`
- B. `try,catch,finally,after`
- C. `try,finally,catch,after`
- D. `try,catch,after`
