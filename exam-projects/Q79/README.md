# 第 79 题 · Q79 · ToLookup 与同键多项

原题号：`Q199`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q199()，返回的字符串是什么？

```csharp
private static string Q199()
{
    var entries = new[] { (User: "u", Value: 2), (User: "u", Value: 3) };
    var lookup = entries.ToLookup(row => row.User, row => row.Value);
    return $"{string.Join(",", lookup["u"])}|{lookup["absent"].Count()}";
}
```

- A. 抛出 ArgumentException。
- B. `2,3|0`
- C. `2|0`
- D. `2,3|1`
