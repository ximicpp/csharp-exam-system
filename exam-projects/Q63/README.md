# 第 63 题 · Q63 · 异常包装与 InnerException

原题号：`Q183`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q183()，返回的字符串是什么？

```csharp
private static string Q183()
{
    Exception original = new FormatException("bad input");
    Exception wrapped = new InvalidOperationException("cannot import", original);
    return $"{wrapped.Message}|{wrapped.InnerException?.Message}";
}
```

- A. `bad input|cannot import`
- B. `cannot import|`
- C. `bad input|bad input`
- D. `cannot import|bad input`
