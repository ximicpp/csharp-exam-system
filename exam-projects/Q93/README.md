# 第 93 题 · Q93 · 通过反射读取特性

原题号：`Q213`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q213()，返回的字符串是什么？

```csharp
[AttributeUsage(AttributeTargets.Class)]
private sealed class Priority213Attribute(int value) : Attribute
{
    public int Value { get; } = value;
}
[Priority213(4)]
private sealed class Job213 { }

private static string Q213()
{
    var attribute = typeof(Job213).GetCustomAttribute<Priority213Attribute>();
    return attribute?.Value.ToString(CultureInfo.InvariantCulture) ?? "missing";
}
```

- A. `4`
- B. `0`
- C. `missing`
- D. 编译失败。
