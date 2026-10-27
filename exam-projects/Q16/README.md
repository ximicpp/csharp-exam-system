# 第 16 题 · Q16 · 集合表达式的展开与后续修改

原题号：`Q136`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q136()，返回的字符串是什么？

```csharp
private static string Q136()
{
    List<int> source = [2, 4];
    int[] packet = [1, .. source, 8];
    source.Add(6);
    return string.Join(",", packet);
}
```

- A. `1,8`
- B. `1,2,4,8`
- C. `1,2,4,6,8`
- D. `2,4,8`
