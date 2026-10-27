# 第 29 题 · Q29 · do 与 while 的执行次数

原题号：`Q149`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q149()，返回的字符串是什么？

```csharp
private static string Q149()
{
    int first = 0;
    int second = 0;
    do { first++; } while (first < 0);
    while (second < 0) { second++; }
    return $"{first},{second}";
}
```

- A. `1,1`
- B. `0,1`
- C. `1,0`
- D. `0,0`
