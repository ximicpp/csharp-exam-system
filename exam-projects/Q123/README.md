# 第 123 题 · Q123 · List 中的 struct 如何写回

原题号：`Q03`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

以下完整程序为什么不能编译？应采用哪种直接修正？

```csharp
using System.Collections.Generic;

public struct Counter
{
    public int Value { get; set; }
}

public static class Program
{
    public static void Main()
    {
        var counters = new List<Counter> { new Counter { Value = 1 } };
        counters[0].Value++;
    }
}
```

- A. 索引器按值返回 Counter；先取出局部副本，修改后赋回 counters[0]。
- B. 这是自增运算对属性的限制；改写为 counters[0].Value = counters[0].Value + 1 即可。
- C. 这是索引表达式的限制；先取出局部 Counter 并递增局部属性即可，不必赋回。
- D. 这是 List 的索引访问限制；改用 foreach (var counter in counters) 并递增其 Value 即可。
