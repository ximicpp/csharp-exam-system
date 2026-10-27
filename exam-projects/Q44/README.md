# 第 44 题 · Q44 · 静态字段与实例状态

原题号：`Q164`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q164()，返回的字符串是什么？

```csharp
private sealed class Ticket164
{
    public static int Created;
    public int Id { get; } = ++Created;
}

private static string Q164()
{
    Ticket164.Created = 0;
    Ticket164 first = new();
    Ticket164 second = new();
    return $"{first.Id},{second.Id},{Ticket164.Created}";
}
```

- A. 编译失败。
- B. `1,2,2`
- C. `1,1,1`
- D. `2,2,2`
