# 第 133 题 · Q133 · 接口参数与受约束的泛型调用

原题号：`Q43`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

InterfaceAndGeneric() 返回什么？哪项解释准确说明接口变量与 ref 泛型参数各自修改了哪份值？

```csharp
private interface ICounter
{
    void Increment();
    int Value { get; }
}

private struct Counter : ICounter
{
    public int Value { get; private set; }
    public void Increment() => Value++;
}

private static void IncrementGeneric<T>(ref T counter) where T : struct, ICounter
    => counter.Increment();
```

```csharp
private static (int Original, int Boxed) InterfaceAndGeneric()
{
    var counter = new Counter();
    ICounter boxed = counter;
    boxed.Increment();
    boxed.Increment();
    IncrementGeneric(ref counter);
    return (counter.Value, boxed.Value);
}
```

- A. (3, 3)：接口变量和 ref 泛型参数都引用原始 counter。
- B. (0, 2)：泛型方法调用接口成员时仍必须装箱，所以原值不变。
- C. (1, 2)：接口变量操作箱内副本，ref 泛型调用操作原始 counter。
- D. (1, 0)：接口上的方法修改的是每次调用时产生的临时副本。
