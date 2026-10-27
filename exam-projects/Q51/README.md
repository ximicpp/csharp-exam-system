# 第 51 题 · Q51 · new() 约束与构造函数

原题号：`Q171`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

为什么 Create<NeedsArg>() 被拒绝？

```csharp
Console.WriteLine(Create<NeedsArg>().Value);
static T Create<T>() where T : new() => new T();
class NeedsArg
{
    public int Value { get; }
    public NeedsArg(int value) => Value = value;
}
```

- A. NeedsArg 没有 public 无参构造器，不满足 new() 约束。
- B. 泛型方法不能创建对象。
- C. 只需把 NeedsArg 类改名为 T。
- D. Value 属性必须可以写。
