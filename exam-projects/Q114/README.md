# 第 114 题 · Q114 · 泛型数学的运算约束

原题号：`Q234`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q234()，返回的字符串是什么？

```csharp
private static T Add234<T>(T left, T right) where T : System.Numerics.INumber<T>
    => left + right;

private static string Q234()
{
    return Add234(1.5m, 2.5m).ToString("F1", CultureInfo.InvariantCulture);
}
```

- A. `1.52.5`
- B. `4.5`
- C. 编译失败。
- D. `4.0`
