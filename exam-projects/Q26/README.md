# 第 26 题 · Q26 · 列表模式与元素数量

原题号：`Q146`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q146()，返回的字符串是什么？

```csharp
private static string Q146()
{
    static bool Valid(string[] args) => args is ["--limit", _];
    return $"{Valid(["--limit", "5"])},{Valid(["--limit", "5", "extra"])}";
}
```

- A. `True,True`
- B. `False,False`
- C. `False,True`
- D. `True,False`
