# 第 145 题 · Q145 · 构造函数体的先后

原题号：`Q81`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

ConstructorOrder() 返回什么？只比较这里的构造函数体。

```csharp
private class Parent
{
    public Parent(List<string> trace) => trace.Add("base");
}
private sealed class Child : Parent
{
    public Child(List<string> trace) : base(trace) => trace.Add("derived");
}
private static string ConstructorOrder()
{
    var trace = new List<string>();
    _ = new Child(trace);
    return string.Join(',', trace);
}
```

- A. "base,derived"
- B. "derived,base"
- C. "base"
- D. 不能编译：构造函数不能传入列表
