# 第 149 题 · Q149 · 命名实参的求值顺序

原题号：`Q89`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

NamedEvaluation() 返回什么？

```csharp
private static (int First, int Second, string Trace) NamedEvaluation()
{
    var trace = new List<string>();
    int Next(string label) { trace.Add(label); return trace.Count; }
    static (int, int) Pair(int first, int second) => (first, second);
    var pair = Pair(second: Next("B"), first: Next("A"));
    return (pair.Item1, pair.Item2, string.Join(',', trace));
}
```

- A. (2, 1, "B,A")
- B. (1, 2, "A,B")
- C. (1, 2, "B,A")
- D. 顺序未定义，依平台而定
