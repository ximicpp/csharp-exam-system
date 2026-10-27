# 第 124 题 · Q124 · record 的相等性与复制深度

原题号：`Q06`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

CopyRecord() 返回什么？

```csharp
private sealed record Report(string Name, List<string> Tags);

private static (bool IndependentEqual, bool CopyEqual, bool SameReport, int OriginalTags) CopyRecord()
{
    var original = new Report("daily", ["draft"]);
    var independent = new Report("daily", ["draft"]);
    var copy = original with { };
    copy.Tags.Add("reviewed");
    return (original == independent, original == copy,
        ReferenceEquals(original, copy), original.Tags.Count);
}
```

- A. (false, true, false, 2)
- B. (true, true, false, 1)
- C. (false, false, false, 2)
- D. (false, true, true, 2)
