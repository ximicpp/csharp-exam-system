# 第 150 题 · Q150 · 默认接口实现的调用视图

原题号：`Q90`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

DefaultInterface() 返回什么？

```csharp
private interface ILabel
{
    string Label() => "default";
}
private sealed class Labelled : ILabel { }
private static (string Label, bool ClassHasNoMethod) DefaultInterface()
{
    ILabel item = new Labelled();
    return (item.Label(), typeof(Labelled).GetMethod("Label") is null);
}
```

- A. ("default", false)
- B. ("default", true)
- C. 不能编译：Labelled 必须实现 Label
- D. 抛出 MissingMethodException
