# 第 122 题 · Q122 · 值类型中的引用字段

原题号：`Q02`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

CopyEnvelope() 返回什么？

```csharp
private struct Envelope
{
    public int Version;
    public List<string> Tags;
}

private static (int AVersion, int BVersion, int ATags, int BTags) CopyEnvelope()
{
    var a = new Envelope { Version = 1, Tags = ["draft"] };
    var b = a;
    b.Version = 8;
    b.Tags.Add("reviewed");
    return (a.Version, b.Version, a.Tags.Count, b.Tags.Count);
}
```

- A. (8, 8, 2, 2)
- B. (1, 8, 1, 2)
- C. (1, 8, 1, 1)
- D. (1, 8, 2, 2)
