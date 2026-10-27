# 第 125 题 · Q125 · 可变哈希键会破坏什么

原题号：`Q08`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

缓存用 Name 作为业务身份，Name 可以改名；下面的实现却直接修改已入表的键对象。需要支持改名后按新名称查找，并处理重名冲突。

以下哪种修改能从设计上恢复键的稳定性？不依赖某次查找恰好成功。

```csharp
private sealed class CacheKey : IEquatable<CacheKey>
{
    public required string Name { get; set; }
    public bool Equals(CacheKey? other) => other is not null && Name == other.Name;
    public override bool Equals(object? obj) => obj is CacheKey other && Equals(other);
    public override int GetHashCode() => StringComparer.Ordinal.GetHashCode(Name);
}

private static Dictionary<CacheKey, string> BuildCache()
{
    var key = new CacheKey { Name = "before" };
    var cache = new Dictionary<CacheKey, string> { [key] = "payload" };
    key.Name = "after";
    return cache;
}
```

- A. 把 key 引用存入 readonly 字段，继续修改该对象的 Name。
- B. 改用入表时的 string 名称作键，改名时检查重名冲突并显式更新新旧映射。
- C. 为 Name 修改和字典操作加同一把锁，继续原地修改已入表键的 Name。
- D. 保留原地改名，规定查找时始终传入原来的 key 对象。

## 动手问题

- 运行原题的 BuildCache，记录入表键当前的 Name、条目数及按原名／新名查找的实际结果。改变两次名称再运行：某一次查找成功能否说明这种键设计可靠？
