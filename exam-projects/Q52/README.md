# 第 52 题 · Q52 · 泛型约束与比较操作

原题号：`Q172`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q172()，返回的字符串是什么？

```csharp
private static T Smaller172<T>(T left, T right) where T : IComparable<T>
    => left.CompareTo(right) <= 0 ? left : right;

private static string Q172()
{
    return Smaller172(8, 3).ToString(CultureInfo.InvariantCulture);
}
```

- A. `8`
- B. `0`
- C. 编译失败。
- D. `3`
