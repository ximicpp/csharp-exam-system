# 第 31 题 · Q31 · params 的空调用与数组调用

原题号：`Q151`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q151()，返回的字符串是什么？

```csharp
private static string Q151()
{
    static int Total(params int[] values) => values.Sum();
    int[] pair = [2, 3];
    return $"{Total()},{Total(pair)},{Total(1, 2, 3)}";
}
```

- A. 编译失败。
- B. `0,2,1`
- C. `0,6,6`
- D. `0,5,6`
