# 第 130 题 · Q130 · 显式接口实现可以改变调用入口

原题号：`Q14`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

ExplicitCall() 返回什么？

```csharp
private interface IFormatter
{
    string Format();
}

private sealed class Formatter : IFormatter
{
    public string Format() => "public";
    string IFormatter.Format() => "interface";
}

private static (string Concrete, string Interface, bool SameObject) ExplicitCall()
{
    var formatter = new Formatter();
    IFormatter view = formatter;
    return (formatter.Format(), view.Format(), ReferenceEquals(formatter, view));
}
```

- A. ("public", "public", true)
- B. ("interface", "interface", true)
- C. ("public", "interface", false)
- D. ("public", "interface", true)
