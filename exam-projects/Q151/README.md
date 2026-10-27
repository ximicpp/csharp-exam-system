# 第 151 题 · Q151 · 实例方法与扩展方法的绑定

原题号：`Q94`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

两个片段处于同一项目与作用域。BindExtension() 返回什么？

```csharp
internal static class QuizStringExtensions
{
    public static bool Contains(this string text, string part) => false;
}
```

```csharp
private static (bool Instance, bool ExplicitStatic) BindExtension() =>
    ("abc".Contains("a"), QuizStringExtensions.Contains("abc", "a"));
```

- A. (false, false)
- B. (true, false)
- C. (true, true)
- D. 不能编译：扩展与实例方法同名冲突
