# 第 38 题 · Q38 · 同一序列的两次枚举

原题号：`Q158`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q158()，返回的字符串是什么？

```csharp
private static IEnumerable<int> Count158()
{
    yield return 1;
    yield return 2;
}

private static string Q158()
{
    IEnumerable<int> values = Count158();
    return $"{string.Join(",", values)}|{string.Join(",", values)}";
}
```

- A. 编译失败。
- B. `1,2|1,2`
- C. `1,2|`
- D. `1|2`
