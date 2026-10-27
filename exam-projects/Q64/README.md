# 第 64 题 · Q64 · 参数异常的参数名

原题号：`Q184`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q184()，返回的字符串是什么？

```csharp
private static string Q184()
{
    static void Validate(int size)
    {
        if (size <= 0) throw new ArgumentOutOfRangeException(nameof(size));
    }
    try { Validate(0); }
    catch (ArgumentOutOfRangeException error) { return error.ParamName ?? "missing"; }
    return "accepted";
}
```

- A. `Validate`
- B. `accepted`
- C. `size`
- D. `0`
