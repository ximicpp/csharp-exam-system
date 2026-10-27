# 02 · 值、引用与 null

目标：准确判断赋值和传参复制了什么。

## 可运行入口

```sh
dotnet run --project samples/LanguageTour -- 02
```

以下代码来自 [Program.cs](../samples/LanguageTour/Program.cs) 的 `Values()` 及对应类型，以及它调用的 [ValueBoundaries.RunValues()](../samples/LanguageTour/ValueBoundaries.cs)。

## struct 复制数据，class 复制引用

类型定义；`{ get; set; }` 声明可读写属性：

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
struct Point(int x, int y)
{
    public int X { get; set; } = x;
    public int Y { get; set; } = y;
}
sealed class Box { public int Value { get; set; } }
```

`Point(int x, int y)` 声明主构造函数参数；`X`、`Y` 是显式声明的属性，初始化式分别使用 `x`、`y`。主构造函数本身不会为普通 class / struct 自动生成公开属性。

赋值后分别修改副本和别名，再尝试在函数内换一个对象：

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
var point = new Point(1, 2);
var copy = point;
copy.X = 9;
var box = new Box { Value = 1 };
var alias = box;
alias.Value = 9;
Replace(box);
Console.WriteLine($"point={point.X}; copy={copy.X}; box={box.Value}");
```

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
static void Replace(Box value) => value = new Box { Value = 100 };
```

```text
point=1; copy=9; box=9
```

`copy` 有自己的 `Point` 数据；`alias` 和 `box` 指向同一个对象。普通参数仍按值传递：`Replace` 复制的是引用，重新赋值只改局部参数，与 Python 参数重新绑定相似。

## struct 的复制也是浅复制

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
readonly record struct Tagged(int Id, List<int> Tags);
```

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
var items = new List<int> { 1 };
var a = new Tagged(1, items);
var b = a;
b.Tags.Add(2);
Console.WriteLine($"shared tags={a.Tags.Count}");
```

```text
shared tags=2
```

`a` 和 `b` 是两份 struct，内部的 `Tags` 却是指向同一列表的引用。`readonly` 不冻结该列表。这里使用的位置 `record struct` 自动生成 `Id`、`Tags` 属性，类型选择见[建模](03-modeling.md)。

## 显式引用参数与 null

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
int number = 1;
Increment(ref number);
string? optional = null;
Console.WriteLine($"ref={number}; length={optional?.Length ?? 0}");
```

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
static void Increment(ref int value) => value++;
```

```text
ref=2; length=0
```

`ref` 让参数成为调用方变量的别名，声明和调用都必须标明。`out` 要求正常返回前赋值；`in` 是只读引用，不保证更快，三者均不转移所有权。

`string?` 是可空分析注解，不改变运行时类型；`int?` 则是 `Nullable<int>`。`?.` 遇 null 返回 null，`??` 提供后备值；`!` 只抑制警告，不做运行时检查。

## List 的 struct 元素要取出、修改、写回

<!-- source: samples/LanguageTour/ValueBoundaries.cs -->
```csharp
var points = new List<Point> { new(1, 2) };
var item = points[0];
item.X = 9;
Console.WriteLine($"list before writeback={points[0].X}");
points[0] = item;
Console.WriteLine($"list after writeback={points[0].X}");
```

```text
list before writeback=1
list after writeback=9
```

`List<T>` 的索引器按值返回元素，`item` 是副本；赋回 `points[0]` 才更新列表。这与 C++ `vector<T>::operator[]` 返回引用不同。直接写 `points[0].X = 9` 是故意不能编译的反例（CS1612）。数组元素则是可写变量，`Point[]` 的 `array[0].X = 9` 可以直接修改。

## default 不调用位置构造函数

非空注解也不改变 `default` 的初始化方式：

<!-- source: samples/LanguageTour/ValueBoundaries.cs -->
```csharp
Tagged empty = default;
Console.WriteLine($"default id={empty.Id}; tags null={empty.Tags is null}");
```

```text
default id=0; tags null=True
```

此代码无需抑制警告。`default` 将 struct 的字段置为默认值，不调用其位置构造函数；因此声明为 `List<int>` 的 `Tags` 仍为 null。保留 struct 时，应把默认值作为一种状态，在使用边界验证；若每个有效实例都必须经过构造校验，可选 class，并在边界拒绝 null。同理，`new Box[3]` 创建三格 null 引用，不会构造三个 `Box`。

## 迁移误区

- C# class 普通传参复制引用，不像 C++ class 按值传参时复制实例。
- 值类型不等于“放在栈上”，存储位置见[内存机制](13-memory.md)。
- `readonly` / `init` 不保证深度不可变；GC 不解决数据竞争，可空分析不替代外部输入校验。

## 练习与验收

任选一种练习方式：[在线引导题 02](online.md) 自动检查新引用与旧别名；或按下面的步骤修改本章示例。

可选练习：修改 [Program.cs](../samples/LanguageTour/Program.cs) 的 `Values()`：将局部函数 `Replace` 的参数改为 `ref Box value`，调用改为 `Replace(ref box)`；给第一条输出末尾增加 `; alias={alias.Value}`。

从仓库根目录运行 `dotnet run --project samples/LanguageTour -- 02`。

验收：退出码为 0，第一条数据输出为 `point=1; copy=9; box=100; alias=9`；后续五条仍为 `shared tags=2`、`ref=2; length=0`、`list before writeback=1`、`list after writeback=9`、`default id=0; tags null=True`。`box` 被重定向，`alias` 仍指向原对象。

主线下一站：[资源与异常](04-resources.md)。按需查阅：[类型与建模](03-modeling.md)。
