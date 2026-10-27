# 第 67 题 · Q67 · 包装读取器是否拥有底层流

原题号：`Q187`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q187()，返回的字符串是什么？

```csharp
private static string Q187()
{
    using MemoryStream stream = new([65]);
    string text;
    using (StreamReader reader = new(stream, Encoding.UTF8, false, 128, leaveOpen: true))
        text = reader.ReadToEnd();
    return $"{text},{stream.CanRead}";
}
```

- A. `,True`
- B. 编译失败。
- C. `A,True`
- D. `A,False`
