# 第 43 题 · Q43 · 对象初始化器与构造函数

原题号：`Q163`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q163()，返回的字符串是什么？

```csharp
private sealed class Settings163
{
    public int Level { get; set; }
    public Settings163() => Level = 3;
}

private static string Q163()
{
    Settings163 options = new() { Level = 8 };
    return options.Level.ToString(CultureInfo.InvariantCulture);
}
```

- A. `8`
- B. `3`
- C. `0`
- D. 编译失败。
