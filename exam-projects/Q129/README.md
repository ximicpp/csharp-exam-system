# 第 129 题 · Q129 · override 与 new 的调用分派

原题号：`Q13`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

DispatchMembers() 返回什么？

```csharp
private class Writer
{
    public virtual string Format() => "base";
    public string Label() => "base";
}

private sealed class JsonWriter : Writer
{
    public override string Format() => "derived";
    public new string Label() => "derived";
}

private static (string Virtual, string BaseView, string DerivedView) DispatchMembers()
{
    Writer writer = new JsonWriter();
    return (writer.Format(), writer.Label(), ((JsonWriter)writer).Label());
}
```

- A. ("derived", "base", "derived")
- B. ("derived", "derived", "derived")
- C. ("base", "base", "derived")
- D. ("derived", "base", "base")
