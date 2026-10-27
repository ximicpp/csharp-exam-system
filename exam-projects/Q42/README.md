# 第 42 题 · Q42 · 私有 setter 与类内状态更新

原题号：`Q162`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q162()，返回的字符串是什么？

```csharp
private sealed class Counter162
{
    public int Count { get; private set; }
    public void Increment() => Count++;
}

private static string Q162()
{
    Counter162 counter = new();
    counter.Increment();
    counter.Increment();
    return counter.Count.ToString(CultureInfo.InvariantCulture);
}
```

- A. `1`
- B. 编译失败。
- C. `2`
- D. `0`
