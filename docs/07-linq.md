# 07 · LINQ 与迭代

目标：区分查询描述、枚举和物化，避免重复工作及资源越界。

## 可运行入口

```sh
dotnet run --project samples/LanguageTour -- 07
```

[Program.cs](../samples/LanguageTour/Program.cs) 的 `Linq()`：先创建查询和快照，再修改源数据。

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
static void Linq()
{
    var numbers = new List<int> { 1, 2, 3 };
    var query = numbers.Where(n => n % 2 != 0).Select(n => n * 10);
    var snapshot = query.ToArray();
    numbers.Add(5);
    Console.WriteLine($"query={string.Join(',', query)}");
    Console.WriteLine($"snapshot={string.Join(',', snapshot)}");
    Console.WriteLine($"iterator={string.Join(',', CountTo(3).Take(2))}");
    static IEnumerable<int> CountTo(int end)
    {
        for (int i = 1; i <= end; i++) yield return i;
    }
}
```

除章节标题外，输出：

```text
query=10,30,50
snapshot=10,30
iterator=1,2
```

`Where` / `Select` 是 `System.Linq.Enumerable` 提供的扩展方法；`numbers.Where(predicate)` 可读作静态调用 `Enumerable.Where(numbers, predicate)`。它们没有修改 List 类型，扩展方法的命名空间须在当前作用域中（本项目通过 implicit using 引入）。

**查询描述不是结果缓存。** `query` 在 `string.Join` 枚举时读取源，因此包含新加入的 5；`snapshot` 在 `ToArray()` 时已求值，因此保留 `10,30`。再次枚举 `query` 会再次筛选、映射。

`CountTo(3)` 返回可枚举序列；枚举时才执行函数体，每次 `yield return` 交出一个值。`Take(2)` 使本次枚举提前结束。需要释放的资源应放在迭代器实际执行的 `using` 作用域中，见[第 14 章](14-execution-model.md)。

| 操作 | 常见执行特征（LINQ to Objects） |
| --- | --- |
| Where / Select / Take | 延迟、逐项产生结果 |
| OrderBy / GroupBy | 延迟开始，通常先缓冲源数据 |
| Count / Sum / Any | 立即求值；具体集合可能有快捷路径 |
| ToArray / ToList | 立即物化，占用额外内存 |

## 迁移误区

- 可类比 Python 生成器、C++ ranges 惰性 view，但 `IEnumerable<T>` 不等于单个 generator：它可能支持重新获取枚举器，也可能包装一次性数据源。
- lambda 中的副作用会随重新枚举重复发生；若调用异步 API，可能重复发请求，见[下一章的 Task 查询实验](08-async.md#linq-查询不是已经创建好的-task-数组)。
- `IQueryable` 可由数据库提供程序翻译，不能照搬本章的内存 LINQ 行为。

## 练习与验收

任选一种练习方式：[在线引导题 07](online.md) 自动检查快照、源变化与重复枚举；或按下面的步骤修改本章示例。

可选练习：修改 [Program.cs](../samples/LanguageTour/Program.cs) 的 `Linq()`：

1. 在 `query` 定义前声明 `int calls = 0;`；让 `Select` 的 lambda 先执行 `calls++`，再返回 `n * 10`。
2. 保留 `snapshot = query.ToArray()` 和 `numbers.Add(5)`，紧接着写 `calls = 0;`，排除创建快照时的两次调用。
3. **替换原有的 `query`、`snapshot` 两条输出**：用 `string.Join(',', ...)` 依次完整枚举 `query` 两次、`snapshot` 两次；每次枚举后输出累计 `calls`。保留 `iterator` 输出。

从仓库根目录运行 `dotnet run --project samples/LanguageTour -- 07`。

验收：退出码为 0；除章节标题外，输出为：

```text
query1=10,30,50; calls=3
query2=10,30,50; calls=6
snapshot1=10,30; calls=6
snapshot2=10,30; calls=6
iterator=1,2
```

下一章：[async / await](08-async.md)。
