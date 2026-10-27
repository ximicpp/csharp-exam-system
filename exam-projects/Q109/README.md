# 第 109 题 · Q109 · 自定义运算符的调用

原题号：`Q229`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q229()，返回的字符串是什么？

```csharp
private readonly record struct Distance229(int Meters)
{
    public static Distance229 operator +(Distance229 left, Distance229 right) => new(left.Meters + right.Meters);
}

private static string Q229()
{
    Distance229 first = new(3);
    Distance229 second = new(4);
    return (first + second).Meters.ToString(CultureInfo.InvariantCulture);
}
```

- A. `12`
- B. `3`
- C. 编译失败。
- D. `7`
