# 第 55 题 · Q55 · 排序比较器与顺序

原题号：`Q175`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q175()，返回的字符串是什么？

```csharp
private static string Q175()
{
    int[] values = [2, 8, 5];
    Array.Sort(values, Comparer<int>.Create((left, right) => right.CompareTo(left)));
    return string.Join(",", values);
}
```

- A. `2,8,5`
- B. 编译失败。
- C. `8,5,2`
- D. `2,5,8`
