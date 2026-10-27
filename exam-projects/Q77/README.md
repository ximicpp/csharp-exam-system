# 第 77 题 · Q77 · 分页的跳过与取出数量

原题号：`Q197`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q197()，返回的字符串是什么？

```csharp
private static string Q197()
{
    int[] items = [10, 20, 30, 40, 50];
    return string.Join(",", items.Skip(2).Take(2));
}
```

- A. `30,40`
- B. `20,30`
- C. `30,40,50`
- D. `10,20`
