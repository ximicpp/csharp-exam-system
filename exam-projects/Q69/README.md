# 第 69 题 · Q69 · Stream.Read 的读取数量

原题号：`Q189`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q189()，返回的字符串是什么？

```csharp
private static string Q189()
{
    using MemoryStream stream = new([7, 8]);
    byte[] buffer = new byte[5];
    int count = stream.Read(buffer, 0, buffer.Length);
    return $"{count},{buffer[0]},{buffer[1]},{buffer[2]}";
}
```

- A. `2,7,8,0`
- B. `5,7,8,0`
- C. `2,7,8,8`
- D. 编译失败。
