# 第 73 题 · Q73 · 展平查询与外侧标签

原题号：`Q193`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q193()，返回的字符串是什么？

```csharp
private static string Q193()
{
    var projects = new[] { (Name: "p", Items: new[] { "a", "b" }), (Name: "q", Items: new[] { "c" }) };
    var rows = projects.SelectMany(project => project.Items, (project, item) => $"{project.Name}:{item}");
    return string.Join(",", rows);
}
```

- A. `p:a,q:b`
- B. `p:a,p:b,p:c`
- C. `p:a,p:b,q:c`
- D. `a,b,c`
