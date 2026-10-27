# 第 105 题 · Q105 · readonly 字段的初始化

原题号：`Q225`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q225()，返回的字符串是什么？

```csharp
private sealed class Token225
{
    public readonly int Id;
    public Token225(int id) => Id = id;
}

private static string Q225()
{
    Token225 value = new(7);
    return value.Id.ToString(CultureInfo.InvariantCulture);
}
```

- A. 编译失败：构造器不能赋值。
- B. `7`
- C. `0`
- D. 编译失败：readonly 只能用于常量。
