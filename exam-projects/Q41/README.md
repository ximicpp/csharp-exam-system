# 第 41 题 · Q41 · 把参数交给基类构造函数

原题号：`Q161`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q161()，返回的字符串是什么？

```csharp
private class Store161
{
    public int Capacity { get; }
    public Store161(int capacity) => Capacity = capacity;
}
private sealed class Worker161 : Store161
{
    public Worker161(int seed) : base(seed + 1) { }
}

private static string Q161()
{
    Worker161 worker = new(3);
    return worker.Capacity.ToString(CultureInfo.InvariantCulture);
}
```

- A. `4`
- B. `3`
- C. `0`
- D. 编译失败。
