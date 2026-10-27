# 第 13 题 · Q13 · 字符单元与 Unicode 标量

原题号：`Q133`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q133()，返回的字符串是什么？

```csharp
private static string Q133()
{
    string text = "A\U0001F600";
    int scalars = 0;
    foreach (Rune rune in text.EnumerateRunes()) scalars++;
    return $"{text.Length},{scalars}";
}
```

- A. `2,1`
- B. `3,2`
- C. `2,2`
- D. `3,3`
