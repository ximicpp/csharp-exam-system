# 第 107 题 · Q107 · 从末尾索引与范围右端

原题号：`Q227`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q227()，返回的字符串是什么？

```csharp
private static string Q227()
{
    int[] values = [1, 2, 3, 4];
    int last = values[^1];
    int[] middle = values[1..^1];
    return $"{last}|{string.Join(",", middle)}";
}
```

- A. `3|2,3`
- B. `4|2,3,4`
- C. `4|1,2,3`
- D. `4|2,3`
