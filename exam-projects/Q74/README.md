# 第 74 题 · Q74 · 分组后的数量求和

原题号：`Q194`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q194()，返回的字符串是什么？

```csharp
private static string Q194()
{
    var entries = new[] { (Team: "a", Count: 2), (Team: "b", Count: 4), (Team: "a", Count: 3) };
    var totals = entries.GroupBy(row => row.Team).OrderBy(group => group.Key, StringComparer.Ordinal)
        .Select(group => $"{group.Key}:{group.Sum(row => row.Count)}");
    return string.Join(",", totals);
}
```

- A. `a:2,b:1`
- B. `a:5,b:4`
- C. `a:2,b:4`
- D. `a:9,b:9`
