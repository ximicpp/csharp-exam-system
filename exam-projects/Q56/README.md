# 第 56 题 · Q56 · Func 的组合调用

原题号：`Q176`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q176()，返回的字符串是什么？

```csharp
private static string Q176()
{
    Func<int, int> twice = value => value * 2;
    Func<int, int> next = value => twice(value) + 1;
    return next(4).ToString(CultureInfo.InvariantCulture);
}
```

- A. 编译失败。
- B. `9`
- C. `8`
- D. `10`
