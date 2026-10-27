# 第 94 题 · Q94 · 表达式树与捕获变量

原题号：`Q214`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q214()，返回的字符串是什么？

```csharp
private static string Q214()
{
    int limit = 3;
    Expression<Func<int, bool>> rule = value => value > limit;
    Func<int, bool> compiled = rule.Compile();
    limit = 8;
    return $"{rule.Body.NodeType},{compiled(5)}";
}
```

- A. 编译失败。
- B. `GreaterThan,False`
- C. `GreaterThan,True`
- D. `Constant,False`
