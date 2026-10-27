# 第 12 题 · Q12 · 插值中的宽度与数字格式

原题号：`Q132`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q132()，返回的字符串是什么？

```csharp
private static string Q132()
{
    int id = 7;
    double score = 2.5;
    return string.Create(CultureInfo.InvariantCulture, $"[{id,5:D3}]/{score:F1}");
}
```

- A. `[007  ]/2.5`
- B. `[00007]/2.5`
- C. `[  007]/3`
- D. `[  007]/2.5`
