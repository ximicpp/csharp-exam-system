# 04 · 资源与异常

目标：区分内存回收与资源释放，明确资源所有者。

## 可运行入口

```sh
dotnet run --project samples/LanguageTour -- 04
```

## 异常路径也先释放资源

[Program.cs](../samples/LanguageTour/Program.cs) 用一行输出标记释放时机：

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
sealed class TracedResource : IDisposable
{
    public void Dispose() => Console.WriteLine("dispose");
}
```

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
static void Resources()
{
    try
    {
        using var resource = new TracedResource();
        Console.WriteLine("work");
        throw new InvalidOperationException("demo");
    }
    catch (InvalidOperationException)
    {
        Console.WriteLine("caught");
    }
}
```

```text
work
dispose
caught
```

`using var` 在离开当前作用域时调用 `Dispose`，所以异常传到 `catch` 前先出现 `dispose`。改成提前 `return` 也经过清理路径；并非最后一次使用后立刻释放。

GC 回收托管内存，`IDisposable` + `using` 管理资源释放，对应 C++ RAII、Python `with`。`using (...) { ... }` 可缩小作用域；`await using` 等待 `IAsyncDisposable` 的异步清理。

## 所有权与异常边界

[LogLens 实战的 CLI 代码](11-project.md) 由调用方创建并释放 StreamReader，Analyzer 借用 TextReader，不负责关闭。坏 JSON 行计数后继续；文件打不开在 CLI 边界报错。重抛当前异常用 `throw;` 保留堆栈。

## 迁移误区

- 普通局部变量离开作用域不会自动调用 Dispose；`~Type()` 是时机不可依赖的终结器，不是 C++ 析构函数。
- `using System.Text;` 是命名空间导入，与资源管理无关。
- Dispose 后引用仍可存在，再次访问的行为取决于类型。

## 练习与验收

任选一种练习方式：[在线引导题 04](online.md) 自动检查成功、EOF、异常路径的资源释放；或按下面的步骤修改本章示例。

可选练习：在 [Program.cs](../samples/LanguageTour/Program.cs) 的 `Resources()` 中，只把 `throw new InvalidOperationException("demo");` 换成 `return;`，保留 `using` 和 `catch`。

从仓库根目录运行 `dotnet run --project samples/LanguageTour -- 04`。

验收：退出码为 0；除章节标题外，只按顺序输出 `work`、`dispose` 两行，不出现 `caught`。提前返回仍经过 `using` 的清理路径。

主线下一站：[LINQ 与迭代](07-linq.md)。按需补充：[泛型与集合](05-generics.md)、[内存与 GC](13-memory.md)。
