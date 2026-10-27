# 第 59 题 · Q59 · 事件订阅与委托退订

原题号：`Q179`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q179()，返回的字符串是什么？

```csharp
private sealed class Publisher179
{
    public event Action? Changed;
    public void Raise() => Changed?.Invoke();
}

private static string Q179()
{
    Publisher179 source = new();
    int calls = 0;
    Action handler = () => calls++;
    source.Changed += handler;
    source.Raise();
    source.Changed -= handler;
    source.Raise();
    return calls.ToString(CultureInfo.InvariantCulture);
}
```

- A. 编译失败。
- B. `1`
- C. `2`
- D. `0`
