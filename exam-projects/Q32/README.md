# 第 32 题 · Q32 · ref 参数与调用方变量

原题号：`Q152`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q152()，返回的字符串是什么？

```csharp
private static string Q152()
{
    static void Advance(ref int position) => position += 2;
    int cursor = 3;
    Advance(ref cursor);
    return cursor.ToString(CultureInfo.InvariantCulture);
}
```

- A. `2`
- B. 编译失败。
- C. `5`
- D. `3`
