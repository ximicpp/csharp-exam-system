# 第 71 题 · Q71 · 查询表达式中的排序与投影

原题号：`Q191`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q191()，返回的字符串是什么？

```csharp
private static string Q191()
{
    int[] scores = [3, 8, 5];
    var query = from score in scores where score > 3 orderby score descending select $"n{score}";
    return string.Join(",", query);
}
```

- A. `8,5`
- B. `n8,n5`
- C. `n5,n8`
- D. `n3,n8,n5`
