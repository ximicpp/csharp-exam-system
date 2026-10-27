# 第 76 题 · Q76 · 排序键相同时的元素顺序

原题号：`Q196`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

使用 LINQ to Objects 执行 Q196()，返回的字符串是什么？

```csharp
private static string Q196()
{
    var tasks = new[] { (Name: "b", Priority: 1), (Name: "a", Priority: 1), (Name: "c", Priority: 0) };
    return string.Join(",", tasks.OrderBy(task => task.Priority).Select(task => task.Name));
}
```

- A. `c,a,b`
- B. `b,a,c`
- C. `a,b,c`
- D. `c,b,a`
