# 第 140 题 · Q140 · 泛型代码共享会合并静态状态吗

原题号：`Q52`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

GenericState() 返回什么？

```csharp
private static class Cache<T>
{
    public static int Hits;
}
```

```csharp
private static (int StringHits, int ObjectHits, bool SameType) GenericState()
{
    Cache<string>.Hits = 7;
    Cache<object>.Hits = 0;
    return (Cache<string>.Hits, Cache<object>.Hits,
        typeof(Cache<string>) == typeof(Cache<object>));
}
```

- A. (0, 0, true)：string 和 object 都是引用类型，因此运行时抹掉类型参数。
- B. (7, 0, false)：两个闭合泛型类型有独立类型身份和静态字段。
- C. (7, 7, false)：类型身份保留，但静态字段属于泛型定义而被共享。
- D. 结果取决于本次 JIT 是否为两个实例化生成不同机器码。
