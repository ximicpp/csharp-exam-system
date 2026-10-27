# 第 50 题 · Q50 · 接口属性与实现类

原题号：`Q170`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q170()，返回的字符串是什么？

```csharp
private interface IIdentified170 { int Id { get; } }
private sealed class Entity170 : IIdentified170
{
    public int Id { get; init; }
    public string Name { get; init; } = "";
}

private static string Q170()
{
    IIdentified170 item = new Entity170 { Id = 6, Name = "job" };
    return item.Id.ToString(CultureInfo.InvariantCulture);
}
```

- A. `0`
- B. 编译失败：实现必须只有 get。
- C. 编译失败：接口不能声明属性。
- D. `6`
