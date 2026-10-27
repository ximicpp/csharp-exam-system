# 第 36 题 · Q36 · 字面量选择哪一个重载

原题号：`Q156`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q156()，返回的字符串是什么？

```csharp
private static string Tag156(int value) => "int";
private static string Tag156(double value) => "double";
private static string Tag156(decimal value) => "decimal";

private static string Q156()
{
    return $"{Tag156(1)}|{Tag156(1.0)}|{Tag156(1.0m)}";
}
```

- A. `int|int|int`
- B. `double|double|double`
- C. 编译失败。
- D. `int|double|decimal`
