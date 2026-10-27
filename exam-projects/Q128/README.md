# 第 128 题 · Q128 · var、object 与 dynamic 的绑定时机

原题号：`Q12`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

BindOverloads() 返回什么？

```csharp
private static string Describe(string value) => "string";
private static string Describe(object value) => "object";

private static (string Inferred, string Object, string Dynamic) BindOverloads()
{
    var inferred = "hello";
    object boxedView = inferred;
    dynamic dynamicView = inferred;
    return (Describe(inferred), Describe(boxedView), Describe(dynamicView));
}
```

- A. ("string", "string", "string")
- B. ("object", "object", "string")
- C. ("string", "object", "string")
- D. ("string", "object", "object")
