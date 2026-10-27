# 第 113 题 · Q113 · 抽象类的公共流程

原题号：`Q233`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q233()，返回的字符串是什么？

```csharp
private abstract class Pipeline233
{
    protected abstract int Step(int value);
    public int Run(int value) => Step(value) + 1;
}
private sealed class Double233 : Pipeline233
{
    protected override int Step(int value) => value * 2;
}

private static string Q233()
{
    Pipeline233 pipeline = new Double233();
    return pipeline.Run(3).ToString(CultureInfo.InvariantCulture);
}
```

- A. `7`
- B. `6`
- C. `4`
- D. 编译失败。
