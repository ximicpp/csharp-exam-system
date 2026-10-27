# 第 7 题 · Q07 · NaN 的两种相等检查

原题号：`Q127`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q127()，返回的字符串是什么？

```csharp
private static string Q127()
{
    double first = double.NaN;
    double second = double.NaN;
    return $"{first == second},{first.Equals(second)},{double.IsNaN(first)}";
}
```

- A. `False,False,True`
- B. `False,True,False`
- C. `False,True,True`
- D. `True,True,True`
