# 第 96 题 · Q96 · Span 切片与后备数组

原题号：`Q216`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q216()，返回的字符串是什么？

```csharp
private static string Q216()
{
    int[] data = [1, 2, 3, 4];
    Span<int> middle = data.AsSpan(1, 2);
    middle[0] = 9;
    return string.Join(",", data);
}
```

- A. `1,2,3,4`
- B. `9,2,3,4`
- C. `1,9,9,4`
- D. `1,9,3,4`
