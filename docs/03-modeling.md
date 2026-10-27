# 03 · 类型与建模

目标：用 class 维护状态边界，按身份、值语义和能力选类型。

## 可运行入口

```sh
dotnet run --project samples/LanguageTour -- 03
```

## record：按成员值相等，with：复制后修改

[Program.cs](../samples/LanguageTour/Program.cs) 的类型定义与 `Modeling()` 调用：

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
sealed record Person(string Name);
```

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
var a = new Person("Ada");
var b = new Person("Ada");
Console.WriteLine($"record equal={a == b}; same object={ReferenceEquals(a, b)}");
var changed = a with { Name = "Grace" };
Console.WriteLine($"original={a.Name}; changed={changed.Name}");
```

```text
record equal=True; same object=False
original=Ada; changed=Grace
```

位置 record 自动生成 `Name` 属性及相等性等成员。这里两份实例按 `Name` 相等，但并非同一对象；`with` 创建副本再设置属性。

## interface：显式契约

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
interface ILabel { string Describe(); }
sealed class Ticket(string id) : ILabel
{
    public string Describe() => $"ticket={id}";
}
```

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
ILabel label = new Ticket("T1");
Console.WriteLine(label.Describe());
```

```text
ticket=T1
```

`Ticket` 声明实现 `ILabel`，编译器检查 `Describe`，不是 Python 鸭子类型。`Ticket(string id)` 是主构造函数，`id` 不像位置 record 的 `Name` 那样自动成为公开属性。

## 集合成员不自动按内容比较，with 也不复制集合

[ValueBoundaries.RunRecords()](../samples/LanguageTour/ValueBoundaries.cs) 由 `Modeling()` 调用，使用一个包含列表的 record：

<!-- source: samples/LanguageTour/ValueBoundaries.cs -->
```csharp
private sealed record Batch(List<int> Items);
```

<!-- source: samples/LanguageTour/ValueBoundaries.cs -->
```csharp
var first = new Batch([1]);
var second = new Batch([1]);
var copied = first with { };
Console.WriteLine($"record collection equal={first == second}");
copied.Items.Add(2);
Console.WriteLine($"with shared={ReferenceEquals(first.Items, copied.Items)}; original count={first.Items.Count}");
```

```text
record collection equal=False
with shared=True; original count=2
```

record 的相等性采用各成员类型的比较规则；`List<T>` 默认比较引用，所以两个内容相同的新列表也让 `first != second`。需要比较元素时可显式使用 `SequenceEqual`，或为模型定义一致的相等性和哈希规则。

`with` 浅复制了 `Items` 引用，修改副本的列表也改变原对象能看到的内容。复制策略与相等性策略是两个问题；`init` 只限制属性重新赋值，并不会冻结列表。

## class：通过构造和方法维护状态

[ModelingBoundaries.cs](../samples/LanguageTour/ModelingBoundaries.cs) 用一个重试额度对象展示普通 class 的 API：

<!-- source: samples/LanguageTour/ModelingBoundaries.cs -->
```csharp
internal sealed class RetryBudget
{
    public RetryBudget(int limit)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(limit);
        Limit = limit;
    }

    public int Limit { get; }
    public int Used { get; private set; }

    public bool TryUse()
    {
        if (Used == Limit) return false;
        Used++;
        return true;
    }
}
```

`Modeling()` 最后调用 `ModelingBoundaries.Run()`，执行：

<!-- source: samples/LanguageTour/ModelingBoundaries.cs -->
```csharp
var budget = new RetryBudget(2);
budget.TryUse();
budget.TryUse();
bool accepted = budget.TryUse();
Console.WriteLine($"budget used={budget.Used}/{budget.Limit}; accepted={accepted}");
try { _ = new RetryBudget(0); }
catch (ArgumentOutOfRangeException) { Console.WriteLine("invalid budget=rejected"); }
```

```text
budget used=2/2; accepted=False
invalid budget=rejected
```

- `Limit { get; }` 在构造函数中赋值；`Used { get; private set; }` 允许调用者读，由类内部写。属性调用访问器，不是公开字段；这里的存储由编译器生成。
- `internal` 把类型限制在本程序集内；`public` 成员仍受类型可见性限制，`private set` 不能从外部赋值。它们是编译器检查的边界，不是 Python 的命名约定。
- 构造函数拒绝无效额度，`TryUse()` 保持 `0 <= Used <= Limit`。只读属性不等于对象不可变；线程间共享时也不会自动获得同步。

## 选型与迁移误区

| 类型 | 适用场景 | 边界 |
| --- | --- | --- |
| `class` | 有身份或生命周期的对象 | 引用语义 |
| `readonly struct` | 坐标、范围等较小的值 | 复制成本随数据大小增长 |
| `record` / `record class` | 按成员值比较的数据模型 | 仍是引用类型 |
| `readonly record struct` | 自动生成相等性等成员的值类型 | 默认值可能违反业务约束 |
| `interface` | 按能力解耦 | 显式契约 |

- class 单继承、多接口。方法默认非虚；重写用 `virtual` / `override`，`new` 仅隐藏成员，见[运行时实验](12-runtime.md)。
- `init` 限制初始化后的赋值，不校验输入，也不冻结内部集合。
- 修改字典键中参与相等性和哈希的状态，会破坏查找。

## 练习与验收

可选练习：在 [Program.cs](../samples/LanguageTour/Program.cs) 中把 `Person` 改为 `Person(string Name, int Age)`；`Modeling()` 中的 `a`、`b` 分别使用 `("Ada", 36)`、`("Ada", 37)`。保留 `with { Name = "Grace" }`，把原有名字输出改成：

```csharp
Console.WriteLine($"original={a.Name}/{a.Age}; changed={changed.Name}/{changed.Age}");
```

从仓库根目录运行 `dotnet run --project samples/LanguageTour -- 03`。

验收：退出码为 0，前三条依次为 `record equal=False; same object=False`、`original=Ada/36; changed=Grace/36`、`ticket=T1`（忽略章节标题）；后面的集合实验与 class 实验保持正文的四条输出。

下一章：[资源与异常](04-resources.md)。
