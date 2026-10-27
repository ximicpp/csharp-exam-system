# 第 111 题 · Q111 · required 成员的初始化

原题号：`Q231`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

为什么 new Item() 被拒绝？

```csharp
var item = new Item();
Console.WriteLine(item.Name);
class Item { public required string Name { get; init; } }
```

- A. 必须把 Name 改为 static。
- B. 创建者没有为 required 的 Name 提供初始化。
- C. init 属性不能属于 class。
- D. required 自动给 Name 赋空字符串，所以错误来自 WriteLine。
