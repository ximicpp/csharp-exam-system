# 06 · 委托、闭包与事件

目标：理解回调的类型、捕获变量和订阅生命周期。

## 可运行入口

```sh
dotnet run --project samples/LanguageTour -- 06
```

以下代码来自 [Program.cs](../samples/LanguageTour/Program.cs) 的 `Delegates()` 及 `Publisher`。

## 捕获变量，不是拍下值的快照

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
int factor = 2;
Func<int, int> scale = x => x * factor;
factor = 3;
Console.WriteLine($"captured={scale(4)}");
```

```text
captured=12
```

`Func<int, int>` 是 int → int 的委托；调用 `scale` 时读到 `factor` 的新值 3。委托有静态签名，可指向方法或 lambda。

## 循环中每轮创建独立变量

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
var actions = new List<Action>();
for (int i = 0; i < 3; i++)
{
    int snapshot = i;
    actions.Add(() => Console.Write(snapshot));
}
foreach (var action in actions) action();
Console.WriteLine();
```

```text
012
```

`Action` 表示无参数、无返回值的回调。每轮声明的 `snapshot` 是独立变量；若直接捕获 `for` 的 `i`，延后调用时三个回调都读到 3。现代 C# 的 `foreach` 迭代变量每轮独立。

## 事件订阅与退订使用同一个处理器

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
sealed class Publisher
{
    public event Action<string>? Message;
    public void Publish(string text) => Message?.Invoke(text);
}
```

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
var source = new Publisher();
Action<string> handler = text => Console.WriteLine($"event={text}");
source.Message += handler;
source.Publish("one");
source.Message -= handler;
source.Publish("two");
```

```text
event=one
```

`event` 允许外部订阅/退订，调用由声明类型控制。保存委托后用 `+=` / `-=` 配对；退订后第二次发布不再输出。重新写一个相同的匿名 lambda 不能可靠退订原回调。

## 迁移误区

- 闭包可延长被引用对象的生命周期；长寿命发布者可能通过订阅留住订阅者。
- 普通事件调用同步执行处理器，异常会传播给调用者；`event` 本身不提供消息队列。
- `static` lambda 让编译器禁止捕获外部局部状态。

## 练习与验收

可选练习：修改 [Program.cs](../samples/LanguageTour/Program.cs) 的 `Delegates()`：删除 `for` 内的 `int snapshot = i;`，把回调改成 `actions.Add(() => Console.Write(i));`，仍在循环结束后调用这三个回调。

从仓库根目录运行 `dotnet run --project samples/LanguageTour -- 06`。

验收：退出码为 0；除章节标题外，依次输出 `captured=12`、`333`、`event=one`，没有 `event=two`。三个委托读取的是同一个循环变量 `i`。

下一章：[LINQ 与迭代](07-linq.md)。
