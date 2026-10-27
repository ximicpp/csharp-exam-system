# 第 24 题 · Q24 · 布尔异或的结果

原题号：`Q144`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q144()，返回的字符串是什么？

```csharp
private static string Q144()
{
    bool a = true;
    bool b = true;
    return $"{a ^ b},{a ^ false},{!a}";
}
```

- A. `False,True,False`
- B. `True,True,False`
- C. `False,False,False`
- D. `False,True,True`
