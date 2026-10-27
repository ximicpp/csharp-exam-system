# 第 14 题 · Q14 · 逐字字符串与转义

原题号：`Q134`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q134()，返回的字符串是什么？

```csharp
private static string Q134()
{
    string path = @"C:\temp\new";
    return $"{path.Contains('\n')},{path.EndsWith(@"\new", StringComparison.Ordinal)}";
}
```

- A. `False,True`
- B. `True,False`
- C. `False,False`
- D. 编译失败。
