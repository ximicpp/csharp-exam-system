# 14 · 编译器如何保存状态

**目标：** 从实际代码的执行顺序，理解属性、`using`、闭包、`yield` 和 `async` 的状态归属。

## 可运行入口

以下定义和调用来自 [ExecutionLesson.cs](../samples/RuntimeLab/ExecutionLesson.cs)。先按[环境说明](setup.md)加载环境，在仓库根目录执行：

```sh
dotnet run --project samples/RuntimeLab -- 14
```

各节输出按下面顺序出现，退出码为 0。**语言保证行为，编译器选择实现方式**；下文的状态机模型不承诺生成类型名称、字段布局或分配次数。

## 属性与 using：隐含的调用

属性可以执行代码，并非一定读取一个字段：

<!-- source: samples/RuntimeLab/ExecutionLesson.cs -->
```csharp
private sealed class Meter
{
    private int reads;
    public int Next => ++reads;
}
```

资源则通过 `Dispose` 提供显式清理：

<!-- source: samples/RuntimeLab/ExecutionLesson.cs -->
```csharp
private sealed class TracedResource : IDisposable
{
    public void Dispose() => Console.WriteLine("using:dispose");
}
```

<!-- source: samples/RuntimeLab/ExecutionLesson.cs -->
```csharp
private static void UseResource()
{
    using var resource = new TracedResource();
    Console.WriteLine("using:body");
}
```

`RunAsync()` 先执行：

<!-- source: samples/RuntimeLab/ExecutionLesson.cs -->
```csharp
var meter = new Meter();
Console.WriteLine($"property:first={meter.Next}; second={meter.Next}");
UseResource();
```

```text
property:first=1; second=2
using:body
using:dispose
```

`Next` 每次读取都执行 getter，所以递增两次；它没有保存“属性结果”的字段。自动属性则由编译器补充后备字段。样例故意展示副作用，普通业务属性应避免这种惊讶。[属性机制](https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/classes-and-structs/properties)

`using var` 在初始化成功后安排清理，可理解为 `try` 包住后续代码、`finally` 调用 `Dispose`。正常退出、`return` 和异常都会清理；构造失败时没有已取得的资源可清理。`Dispose` 不会把托管对象从内存删除。[using 转换](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/using)

## 闭包：方法返回，变量仍由委托使用

<!-- source: samples/RuntimeLab/ExecutionLesson.cs -->
```csharp
private static Func<int> CreateCounter(int start)
{
    int count = start;
    return () => ++count;
}
```

创建两个互相独立的计数器：

<!-- source: samples/RuntimeLab/ExecutionLesson.cs -->
```csharp
var next = CreateCounter(0);
var other = CreateCounter(10);
Console.WriteLine($"closure:first={next()}; second={next()}; other={other()}");
```

```text
closure:first=1; second=2; other=11
```

委托仍需访问 `count`，其状态必须活过 `CreateCounter` 调用。常见实现是生成一个保存 `count` 的环境对象，让委托关联该对象。同一次调用中捕获同一变量的委托共享变量；不同调用各有状态。这既不是失效的 C++ 栈引用，也不是整数快照。

捕获对象引用也会保留对象图；长寿命事件或队列中的委托可能因此留住大量数据。`static` lambda 禁止捕获外部局部变量和实例状态，让这类依赖在编译期显现。[捕获规则](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/lambda-expressions#capture-of-outer-variables-and-variable-scope-in-lambda-expressions)

## yield：MoveNext 恢复，Dispose 清理

迭代器在两次产出之间保存执行位置：

<!-- source: samples/RuntimeLab/ExecutionLesson.cs -->
```csharp
private static IEnumerable<int> TraceSequence()
{
    Console.WriteLine("iterator:enter");
    try
    {
        yield return 10;
        Console.WriteLine("iterator:resume");
        yield return 20;
    }
    finally
    {
        Console.WriteLine("iterator:finally");
    }
}
```

调用方只取第一个元素就释放枚举器：

<!-- source: samples/RuntimeLab/ExecutionLesson.cs -->
```csharp
var sequence = TraceSequence();
Console.WriteLine("iterator:created");
using (var iterator = sequence.GetEnumerator())
{
    bool moved = iterator.MoveNext();
    Console.WriteLine($"iterator:moved={moved}; current={iterator.Current}");
} // 提前 Dispose：执行挂起位置所属的 finally，不执行下一次 yield。
Console.WriteLine("iterator:disposed");
```

```text
iterator:created
iterator:enter
iterator:moved=True; current=10
iterator:finally
iterator:disposed
```

`TraceSequence()` 只取得可枚举对象，首次 `MoveNext()` 才执行方法体；`yield return` 设置当前值、保存位置并返回 `true`。下次 `MoveNext()` 会从暂停处继续。此处却先 `Dispose`，所以执行已进入的 `try` 对应的 `finally`，不执行 `iterator:resume`。

常见实现是枚举器对象保存当前位置、当前值及跨暂停点使用的数据。暂停不等于释放，文件流等资源可以随状态保留。`foreach` 会为支持释放的枚举器安排清理；手写 `MoveNext` 时需自己配对 `using` 或 `try/finally`。[yield 的执行与释放](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/yield)

## async：等待项完成后恢复

这个方法要在 `await` 后继续使用 `saved`：

<!-- source: samples/RuntimeLab/ExecutionLesson.cs -->
```csharp
private static async Task<int> ResumeAsync(Task gate)
{
    int saved = 40;
    Console.WriteLine("async:before");
    await gate;
    Console.WriteLine("async:after");
    return saved + 2;
}
```

用手动完成的 Task 控制挂起与恢复，不靠计时：

<!-- source: samples/RuntimeLab/ExecutionLesson.cs -->
```csharp
var gate = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
var pending = ResumeAsync(gate.Task);
Console.WriteLine($"async:completed={pending.IsCompleted}");
gate.SetResult();
int result = await pending;
Console.WriteLine($"async:result={result}");
```

```text
async:before
async:completed=False
async:after
async:result=42
```

调用 `ResumeAsync` 立即执行到 `await gate`。此时等待项未完成，于是保存恢复位置和所需状态、登记后续动作，向调用者交还未完成的 Task。`SetResult()` 放行后才恢复；等待项如果已完成，`await` 会直接取得结果继续。[await 行为](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/await)

编译器通常生成状态机，用字段保存跨暂停点使用的数据，通过构建器把返回值、异常或取消传到结果 Task。因此状态可以存活，而原线程无需停在调用栈上等待。具体字段、常量和分配仍可能被优化。[状态机](https://learn.microsoft.com/en-us/dotnet/api/system.runtime.compilerservices.asyncstatemachineattribute?view=net-10.0)

`RunContinuationsAsynchronously` 避免在 `SetResult` 调用中内联执行已登记的后续动作，不会强制已完成 Task 上的 `await` 挂起。上面的顺序来自完成关系，不依赖线程编号或延迟。[任务选项](https://learn.microsoft.com/en-us/dotnet/api/system.threading.tasks.taskcreationoptions?view=net-10.0)

| 机制 | 谁触发执行 / 恢复 | 状态保存在何处（常见实现） |
| --- | --- | --- |
| 闭包 | 调用委托 | 委托关联的捕获环境 |
| `yield` | 调用方执行 `MoveNext` | 枚举器对象 |
| `async` | 开始调用；等待项完成后恢复 | 异步状态机 |

## 迁移误区

- 源码花括号不能决定所有对象的寿命；捕获和暂停都可能延长引用的保留时间。
- `async` 不创建专属线程，也不保证每次 `await` 都暂停、切线程或新增堆分配。
- `using` 跨越 `await` 或 `yield` 时，暂停不等于退出作用域；资源可能持续打开。

## 练习与验收

可选：验证已完成的等待项不会使方法暂停。

1. 修改上述文件的 `RunAsync()`，把现有 `gate.SetResult();` **移动**到 `var pending = ResumeAsync(gate.Task);` 前一行。只保留一次 `SetResult` 调用。
2. 重新运行同一条命令。验收：退出码为 0，前九行不变，最后四行严格变为：

```text
async:before
async:after
async:completed=True
async:result=42
```

这说明 `ResumeAsync` 在返回给调用者前已执行完毕；`RunContinuationsAsynchronously` 没有强迫这次 `await` 挂起。失败时先检查是否误保留了第二次 `SetResult`，以及移动位置是否在调用 `ResumeAsync` 之前。[参考答案](../exercises/solutions.md#14--已完成的-await)

资料核对日期：2026-09-28。回看：[回调](06-delegates.md)、[LINQ](07-linq.md)、[异步](08-async.md)。
