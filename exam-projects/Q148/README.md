# 第 148 题 · Q148 · 可选参数与虚调用分两步

原题号：`Q88`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

OptionalDispatch() 返回什么？

```csharp
private class BaseSender
{
    public virtual int Send(int retries = 10) => retries;
}
private sealed class DerivedSender : BaseSender
{
    public override int Send(int retries = 20) => retries;
}
private static (int ViaBase, int ViaDerived) OptionalDispatch()
{
    var derived = new DerivedSender();
    BaseSender viaBase = derived;
    return (viaBase.Send(), derived.Send());
}
```

- A. (20, 20)
- B. (10, 10)
- C. 不能编译：override 不能声明默认值
- D. (10, 20)
