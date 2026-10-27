# 第 11 题 · Q11 · 字符串 Replace 的结果

原题号：`Q131`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q131()，返回的字符串是什么？

```csharp
private static string Q131()
{
    string name = "draft.txt";
    _ = name.Replace("draft", "final", StringComparison.Ordinal);
    string renamed = name.Replace("draft", "final", StringComparison.Ordinal);
    return $"{name}|{renamed}";
}
```

- A. `draft.txt|final.txt`
- B. `final.txt|final.txt`
- C. `draft.txt|draft.txt`
- D. `final.txt|draft.txt`
