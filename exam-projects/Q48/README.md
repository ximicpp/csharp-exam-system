# 第 48 题 · Q48 · override 内的 base 调用

原题号：`Q168`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q168()，返回的字符串是什么？

```csharp
private class Base168
{
    public virtual string Name() => "base";
}
private sealed class Derived168 : Base168
{
    public override string Name() => base.Name() + "+derived";
}

private static string Q168()
{
    Base168 value = new Derived168();
    return value.Name();
}
```

- A. `base+derived`
- B. `base`
- C. `derived`
- D. 编译失败。
