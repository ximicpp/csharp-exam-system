# 05 · 泛型与集合

目标：理解泛型约束，按访问需求选集合。

## 可运行入口

```sh
dotnet run --project samples/LanguageTour -- 05
```

## 约束赋予操作能力，比较器定义键的相等性

[Program.cs](../samples/LanguageTour/Program.cs) 的完整 `Generics()`：

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
static void Generics()
{
    Console.WriteLine($"max={Max(3, 7)}");
    var counts = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase)
    {
        ["GET"] = 2
    };
    Console.WriteLine($"found={counts.TryGetValue("get", out var count)}; count={count}");
    Console.WriteLine($"distinct={new HashSet<int> { 1, 1, 2 }.Count}");
    static T Max<T>(T a, T b) where T : IComparable<T> => a.CompareTo(b) >= 0 ? a : b;
}
```

```text
max=7
found=True; count=2
distinct=2
```

`where T : IComparable<T>` 让方法体能调用 `CompareTo`。C# 泛型按声明的约束检查方法体，并保留运行时类型信息；不像模板那样等调用方提供了成员才算合法。无约束的 `T` 不能直接使用 `a + b`。

字典用 `OrdinalIgnoreCase`，所以 `get` 找到 `GET`；`TryGetValue` 同时返回成功标志和值。HashSet 按相等性去重，两个 `1` 只计一次；哈希集合要求相等性与哈希一致。

## 集合选择与迁移误区

- 顺序存储用 `List<T>`，按键查找用 `Dictionary<K,V>`，去重用 `HashSet<T>`。`List<int>` 存储 int 无需逐元素装箱。
- 字典索引读取缺失键会抛异常，不像 C++ `map::operator[]` 插入默认值；机器标识的字符串键常用 `Ordinal` / `OrdinalIgnoreCase`。
- `T[]` 是引用类型，变量赋值不复制元素。`IReadOnlyList<T>` 只限制接口的写入能力，不保证底层数据不变。
- `IEnumerable<T>` 只承诺可枚举，不保证下标、重复枚举或低成本 Count。
- foreach 中修改同一个 List 的结构通常导致枚举失败；普通集合不保证并发修改安全。

## 练习与验收

可选练习：在 [Program.cs](../samples/LanguageTour/Program.cs) 末尾的类型定义区添加 `readonly record struct Score(int Value)`，在类型声明中列出 `IComparable<Score>`，并用 `public int CompareTo(Score other)` 实现接口。按 `Value` 的大小返回负数、0 或正数；比较结果只约定符号，不要求只能返回 -1 或 1。不要用整数相减判断顺序，极端值会溢出。

在 `Generics()` 内、现有局部函数 `Max<T>` 定义之前加入调用，保留原代码：

```csharp
Console.WriteLine($"score max={Max(new Score(3), new Score(7)).Value}");
Console.WriteLine($"score reverse={Max(new Score(7), new Score(3)).Value}");
Console.WriteLine($"score edge={Max(new Score(int.MinValue), new Score(int.MaxValue)).Value}");
Console.WriteLine($"score edge reverse={Max(new Score(int.MaxValue), new Score(int.MinValue)).Value}");
Console.WriteLine($"score order={new Score(3).CompareTo(new Score(7)) < 0},{new Score(7).CompareTo(new Score(3)) > 0}");
Console.WriteLine($"score equal={new Score(7).CompareTo(new Score(7))}");
```

从仓库根目录运行 `dotnet run --project samples/LanguageTour -- 05`。

验收：退出码为 0，原三条输出不变，随后依次为：

```text
score max=7
score reverse=7
score edge=2147483647
score edge reverse=2147483647
score order=True,True
score equal=0
```

两个顺序都要测试：仅在“不等时返回负数”的错误实现，会在逆序和 `score order` 检查中暴露。

再临时移除 `Score` 声明中的 `: IComparable<Score>`，保留 `CompareTo` 方法。执行 `dotnet build samples/LanguageTour` 应非零退出，并报告 `CS0315`：仅有同名方法不满足接口约束。这是故意不能编译的变体；恢复接口后重跑本章，必须再次满足上述验收。

下一章：[委托、闭包与事件](06-delegates.md)。
