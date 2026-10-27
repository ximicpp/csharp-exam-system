# 第 104 题 · Q104 · null-forgiving 与可空分析

原题号：`Q224`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q224()，返回的字符串是什么？

```csharp
private static string Q224()
{
    string? raw = null;
    string assumed = raw!;
    return (assumed is null).ToString();
}
```

- A. 编译失败。
- B. `True`
- C. `False`
- D. 抛出 InvalidOperationException。
