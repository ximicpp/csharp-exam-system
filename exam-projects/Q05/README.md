# 第 5 题 · Q05 · 缩窄转换是否检测溢出

原题号：`Q125`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q125()，返回的字符串是什么？

```csharp
private static string Q125()
{
    int value = 300;
    byte wrapped = unchecked((byte)value);
    try { _ = checked((byte)value); }
    catch (OverflowException) { return $"{wrapped},overflow"; }
    return "no-error";
}
```

- A. `255,overflow`
- B. `300,overflow`
- C. `44,overflow`
- D. `44,no-error`
