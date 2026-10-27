# 第 8 题 · Q08 · 可空整数的运算

原题号：`Q128`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q128()，返回的字符串是什么？

```csharp
private static string Q128()
{
    int? reading = null;
    int? adjusted = reading + 2;
    return $"{adjusted.HasValue},{adjusted.GetValueOrDefault()}";
}
```

- A. `False,0`
- B. `True,2`
- C. `True,0`
- D. 编译失败。
