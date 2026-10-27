# 第 35 题 · Q35 · 解构赋值与弃元

原题号：`Q155`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q155()，返回的字符串是什么？

```csharp
private static string Q155()
{
    int count = 9;
    (string status, _) = ("ready", 3);
    return $"{status},{count}";
}
```

- A. `ready,3`
- B. `3,9`
- C. 编译失败。
- D. `ready,9`
