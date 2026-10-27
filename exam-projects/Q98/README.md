# 第 98 题 · Q98 · 扩展属性与对象成员

原题号：`Q218`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q218()，返回的字符串是什么？

```csharp
internal static class MicrosoftTextExtensions
{
    extension(string text)
    {
        public bool HasContent => text.Length > 0;
    }
}
```

```csharp
private static string Q218()
{
    string text = "go";
    return $"{text.HasContent},{"".HasContent}";
}
```

- A. `True,True`
- B. `False,False`
- C. 编译失败。
- D. `True,False`
