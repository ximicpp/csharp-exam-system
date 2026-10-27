# 第 86 题 · Q86 · 异步序列的枚举

原题号：`Q206`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

执行 await Q206()，得到的字符串是什么？

```csharp
private static async IAsyncEnumerable<int> Read206()
{
    yield return 1;
    await Task.CompletedTask;
    yield return 2;
}

private static async Task<string> Q206()
{
    int total = 0;
    await foreach (int value in Read206()) total += value;
    return total.ToString(CultureInfo.InvariantCulture);
}
```

- A. 编译失败。
- B. `3`
- C. `1`
- D. `2`
