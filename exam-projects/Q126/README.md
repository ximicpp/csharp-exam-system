# 第 126 题 · Q126 · 泛型方法中的成员访问

原题号：`Q09`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

这段程序不能编译。若希望 IsNewer 支持实现 IRevisioned 的类型，并保留静态类型检查，哪项修正正确？

```csharp
using System;

public interface IRevisioned
{
    int Revision { get; }
}

public sealed record Document(int Revision) : IRevisioned;

public static class Program
{
    public static bool IsNewer<T>(T left, T right) => left.Revision > right.Revision;

    public static void Main() =>
        Console.WriteLine(IsNewer(new Document(2), new Document(1)));
}
```

- A. 仅在 Main 显式指定 IsNewer 的类型实参为 Document，泛型方法体便会获得 Document 成员。
- B. 给方法添加 where T : class，编译器便会允许任意实例成员。
- C. 给方法添加 where T : IRevisioned，让方法体按接口契约读取 Revision。
- D. 只把调用移到其他程序集，方法体的检查会延迟到运行时。
