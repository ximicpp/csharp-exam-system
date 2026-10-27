# 第 53 题 · Q53 · 序列接口的协变

原题号：`Q173`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

调用 Q173()，返回的字符串是什么？

```csharp
private class Animal173 { }
private sealed class Cat173 : Animal173 { }

private static string Q173()
{
    IEnumerable<Cat173> cats = new List<Cat173> { new() };
    IEnumerable<Animal173> animals = cats;
    return animals.Single().GetType().Name;
}
```

- A. `Object`
- B. 编译失败。
- C. `Cat173`
- D. `Animal173`
