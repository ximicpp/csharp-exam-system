# 第 40 题 · Q40 · yield 与异常处理块

原题号：`Q160`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

以下完整程序为什么不能编译？哪项准确指出所示 yield return 所在位置违反的规则？

```csharp
using System.Collections.Generic;
foreach (int item in Read()) Console.WriteLine(item);
static IEnumerable<int> Read()
{
    try { yield return 1; }
    catch (InvalidOperationException) { yield break; }
}
```

- A. 迭代器必须声明为 async。
- B. catch 中的 yield break 总是不合法。
- C. 带 catch 的 try 块内不能使用 yield return。
- D. yield return 不能返回整数。
