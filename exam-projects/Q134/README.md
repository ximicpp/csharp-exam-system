# 第 134 题 · Q134 · Span 与 ReadOnlySpan 的数据关系

原题号：`Q44`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 SharedViews() 返回什么？

```csharp
private static (int ReadOnlyFirst, int TailValue) SharedViews()
{
    int[] data = [10, 20, 30];
    Span<int> middle = data.AsSpan(1, 2);
    ReadOnlySpan<int> readOnly = middle;
    middle[0] = 99;
    data[2] = 7;
    return (readOnly[0], middle[1]);
}
```

- A. (20, 30)：Span 切片与 ReadOnlySpan 转换都复制数据。
- B. (20, 7)：只有 ReadOnlySpan 转换会创建不可变快照。
- C. 编译失败：存在 ReadOnlySpan 时，编译器禁止其他别名写入数组。
- D. (99, 7)：两个 Span 都是同一底层数组的视图。
