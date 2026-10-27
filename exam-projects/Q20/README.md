# 第 20 题 · Q20 · 集合重复插入的返回值

原题号：`Q140`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q140()，返回的字符串是什么？

```csharp
private static string Q140()
{
    HashSet<int> seen = [5];
    bool first = seen.Add(8);
    bool duplicate = seen.Add(5);
    return $"{first},{duplicate},{seen.Count}";
}
```

- A. `True,True,3`
- B. `True,False,1`
- C. `False,False,1`
- D. `True,False,2`
