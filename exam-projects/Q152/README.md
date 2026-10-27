# 第 152 题 · Q152 · 多播委托的返回值

原题号：`Q98`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

InvokeDelegates() 返回什么？假设两个处理器均不抛异常。

```csharp
private static (int Result, string Trace) InvokeDelegates()
{
    var trace = new List<string>();
    Func<int> handler = () => { trace.Add("first"); return 5; };
    handler += () => { trace.Add("second"); return 10; };
    return (handler(), string.Join(',', trace));
}
```

- A. (5, "first")
- B. (10, "first,second")
- C. (15, "first,second")
- D. 不能编译：只有 Action 可以组合
