# 第 57 题 · Q57 · static lambda 的参数与使用

原题号：`Q177`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q177()，返回的字符串是什么？

```csharp
private static string Q177()
{
    int[] values = [2, 3];
    return string.Join(",", values.Select(static value => value * value));
}
```

- A. `2,3`
- B. 编译失败：static lambda 不能有参数。
- C. 编译失败：不能传给 Select。
- D. `4,9`
