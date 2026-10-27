# 第 34 题 · Q34 · 局部函数的声明与调用

原题号：`Q154`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q154()，返回的字符串是什么？

```csharp
private static string Q154()
{
    int result = Factorial(4);
    return result.ToString(CultureInfo.InvariantCulture);

    static int Factorial(int n) => n <= 1 ? 1 : n * Factorial(n - 1);
}
```

- A. `4`
- B. `1`
- C. 编译失败。
- D. `24`
