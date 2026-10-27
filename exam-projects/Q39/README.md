# 第 39 题 · Q39 · foreach 退出与迭代器清理

原题号：`Q159`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q159()，返回的字符串是什么？

```csharp
private static IEnumerable<int> Read159(List<string> log)
{
    try { yield return 1; yield return 2; }
    finally { log.Add("close"); }
}

private static string Q159()
{
    List<string> log = [];
    foreach (int value in Read159(log)) { log.Add($"item{value}"); break; }
    return string.Join(",", log);
}
```

- A. `item1,close`
- B. `item1`
- C. `item1,item2,close`
- D. `close,item1`
