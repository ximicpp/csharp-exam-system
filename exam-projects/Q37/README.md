# 第 37 题 · Q37 · yield break 与枚举结束

原题号：`Q157`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q157()，返回的字符串是什么？

```csharp
private static IEnumerable<int> Read157()
{
    foreach (int value in new[] { 2, 4, 0, 8 })
    {
        if (value == 0) yield break;
        yield return value;
    }
}

private static string Q157()
{
    return string.Join(",", Read157());
}
```

- A. `2,4,8`
- B. `2,4,0,8`
- C. 编译失败。
- D. `2,4`
