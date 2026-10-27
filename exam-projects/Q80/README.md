# 第 80 题 · Q80 · 查询创建与源集合修改

原题号：`Q200`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q200()，返回的字符串是什么？

```csharp
private static string Q200()
{
    List<int> source = [1, 2];
    var query = source.Where(value => value > 1);
    source.Add(3);
    int[] snapshot = query.ToArray();
    source.Add(4);
    return string.Join(",", snapshot);
}
```

- A. `2,3,4`
- B. `1,2,3`
- C. `2,3`
- D. `2`
