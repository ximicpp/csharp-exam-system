# 第 103 题 · Q103 · default 与显式结构构造器

原题号：`Q223`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q223()，返回的字符串是什么？

```csharp
private struct Options223
{
    public int Limit;
    public Options223() => Limit = 5;
}

private static string Q223()
{
    Options223 constructed = new();
    Options223 zeroed = default;
    return $"{constructed.Limit},{zeroed.Limit}";
}
```

- A. 编译失败。
- B. `5,0`
- C. `5,5`
- D. `0,0`
