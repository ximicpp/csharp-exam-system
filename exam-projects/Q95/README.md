# 第 95 题 · Q95 · dynamic 的成员绑定

原题号：`Q215`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q215()，返回的字符串是什么？

```csharp
private static string Q215()
{
    dynamic text = "hello";
    try { _ = text.MissingMember(); }
    catch (Microsoft.CSharp.RuntimeBinder.RuntimeBinderException) { return "binding failed"; }
    return "success";
}
```

- A. `success`
- B. 编译失败。
- C. 抛出 NullReferenceException。
- D. `binding failed`
