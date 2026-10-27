# 第 54 题 · Q54 · 回调参数的逆变

原题号：`Q174`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q174()，返回的字符串是什么？

```csharp
private static string Q174()
{
    string log = "";
    Action<object> record = value => log = value.GetType().Name;
    Action<string> acceptText = record;
    acceptText("hello");
    return log;
}
```

- A. 编译失败。
- B. `String`
- C. `Object`
- D. `hello`
