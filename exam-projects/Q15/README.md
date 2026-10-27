# 第 15 题 · Q15 · 新数组里的初始元素

原题号：`Q135`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q135()，返回的字符串是什么？

```csharp
private static string Q135()
{
    int[] counts = new int[2];
    string?[] names = new string?[2];
    return $"{counts[0]},{names[0] is null},{counts.Length}";
}
```

- A. 编译失败。
- B. `0,True,2`
- C. `0,False,2`
- D. `2,True,2`
