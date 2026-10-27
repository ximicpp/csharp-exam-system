# 01 · 语法速查

目标：读懂 C# 的类型推断、解构、索引和模式匹配。

## 可运行入口

```sh
dotnet run --project samples/LanguageTour -- 01
```

## 从代码看语法

[Program.cs](../samples/LanguageTour/Program.cs) 的完整 `Syntax()`：

<!-- source: samples/LanguageTour/Program.cs -->
```csharp
static void Syntax()
{
    var n = 7; // 编译期就是 int，不是 dynamic。
    Console.WriteLine($"division={n / 2}; real={n / 2.0}");
    Console.WriteLine($"parsed={int.TryParse("42", out var value)}; value={value}");
    var (name, count) = ("log", 3);
    Console.WriteLine($"{name}:{count}; last={new[] { 2, 4, 6 }[^1]}");
    Console.WriteLine($"category={Category(503)}");
    Console.WriteLine($"string equality={new string('x', 1) == "x"}");
    static string Category(int status) => status switch
    {
        >= 500 => "server", >= 400 => "client", _ => "ok"
    };
}
```

输出（省略章节标题，下同）：

```text
division=3; real=3.5
parsed=True; value=42
log:3; last=6
category=server
string equality=True
```

- `var` 在编译期推断类型，类似 C++ `auto`；`n` 始终是 `int`。`7 / 2` 是整数除法，`7 / 2.0` 是浮点除法。
- `$"..."` 插值；`out var value` 声明输出参数；`(name, count)` 解构值元组；`[^1]` 从末尾取第一个元素。
- `Category` 是局部函数，`=>` 后的 switch 表达式返回第一个匹配分支的结果；`_` 是兜底分支。

项目用顶层语句生成程序入口，类型声明放在其后。属性的 `get` / `set` 见[下一章的 Point](02-values.md)。

## 后续代码中会遇到的简写

| 写法 | 阅读方式 | 实际代码 |
| --- | --- | --- |
| `new(1, 2)` | 从赋值或参数的目标类型推断要构造的类型 | [02 的 List 元素](02-values.md) |
| `[1, 2]` | 集合表达式；目标类型决定构造数组、List 等，不等于固定的 Python list | [03 的集合 record](03-modeling.md) |
| `record Batch(List<int> Items)` | 位置 record，自动生成属性与相等性成员 | [03 建模](03-modeling.md) |
| `"""..."""` | 原始字符串，JSON 中的双引号无需逐个转义；多行内容的公共缩进由结束分隔符决定 | [09 的 JSON 测试输入](09-engineering.md) |

这些是当前示例使用的语言写法；先按右栏看实际代码即可，暂不需要展开版本特性列表。

## 迁移误区

- `int` 是 32 位整数；任意精度用 `BigInteger`，需检测溢出时用 `checked`。
- 负数整数除法朝零截断，与 Python `//` 不同。
- 条件必须是 `bool`，没有整数或集合的隐式真值判断；`dynamic` 才在运行时绑定。
- `string` 不可变，`==` 比较内容；普通 class 未重载 `==` 时比较引用。
- `[^1]` 不会让空集合安全；范围较宽的 switch 分支可能使后续分支不可达。

## 练习与验收

可选练习：修改 [Program.cs](../samples/LanguageTour/Program.cs) 的 `Syntax()`，给局部函数 `Category` 添加 `>= 300 => "redirect"` 分支。保留原有分支，在现有 `category` 输出后增加：

```csharp
Console.WriteLine($"categories={Category(200)},{Category(302)},{Category(404)},{Category(503)}");
```

从仓库根目录运行 `dotnet run --project samples/LanguageTour -- 01`。

验收：退出码为 0，新增一行 `categories=ok,redirect,client,server`。若出现 CS8510，检查宽范围分支是否覆盖了后面的窄范围分支。

下一章：[值、引用与 null](02-values.md)。
