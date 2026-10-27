# 第 28 题 · Q28 · 跳过一项与终止循环

原题号：`Q148`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q148()，返回的字符串是什么？

```csharp
private static string Q148()
{
    int total = 0;
    foreach (int value in new[] { 3, -2, 4, 0, 9 })
    {
        if (value < 0) continue;
        if (value == 0) break;
        total += value;
    }
    return total.ToString(CultureInfo.InvariantCulture);
}
```

- A. `7`
- B. `16`
- C. `5`
- D. `3`
