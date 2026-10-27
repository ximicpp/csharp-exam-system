# 第 45 题 · Q45 · 记录相等与普通类相等

原题号：`Q165`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q165()，返回的字符串是什么？

```csharp
private sealed record Person165(string Name);
private sealed class Plain165(string name)
{
    public string Name { get; } = name;
}

private static string Q165()
{
    Person165 a = new("Lin");
    Person165 b = new("Lin");
    Plain165 x = new("Lin");
    Plain165 y = new("Lin");
    return $"{a == b},{x == y}";
}
```

- A. `True,False`
- B. `True,True`
- C. `False,False`
- D. `False,True`
