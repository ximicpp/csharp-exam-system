# 第 9 题 · Q09 · 可空文本链上的空内容

原题号：`Q129`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q129()，返回的字符串是什么？

```csharp
private static string Q129()
{
    string? absent = null;
    string? blank = "   ";
    return $"{absent?.Trim().Length ?? -1},{blank?.Trim().Length ?? -1}";
}
```

- A. `0,0`
- B. 编译失败。
- C. `-1,0`
- D. `-1,-1`
