# 第 78 题 · Q78 · 空序列上的 All 与 Any

原题号：`Q198`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q198()，返回的字符串是什么？

```csharp
private static string Q198()
{
    int[] values = [];
    return $"{values.All(value => value > 0)},{values.Any()}";
}
```

- A. 编译失败。
- B. `True,False`
- C. `False,False`
- D. `True,True`
