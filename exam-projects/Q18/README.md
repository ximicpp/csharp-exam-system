# 第 18 题 · Q18 · 字典中的零与缺失键

原题号：`Q138`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q138()，返回的字符串是什么？

```csharp
private static string Q138()
{
    Dictionary<string, int> config = new() { ["retry"] = 0 };
    bool found = config.TryGetValue("retry", out int retry);
    bool missing = config.TryGetValue("timeout", out int timeout);
    return $"{found},{retry},{missing},{timeout}";
}
```

- A. 编译失败。
- B. `True,0,False,0`
- C. `False,0,False,0`
- D. `True,0,True,0`
