# 第 158 题 · Q158 · 任务查询的重复枚举

原题号：`Q36`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

Q36() 返回什么？怎样才能让两次 WhenAll 等待同一批任务？

```csharp
private static async Task<(int Before, int First, int Second)> Q36()
{
    int starts = 0;
    Task<int> FetchAsync(int id)
    {
        starts++;
        return Task.FromResult(id);
    }
    int[] ids = [1, 2, 3];
    IEnumerable<Task<int>> requests = ids.Select(FetchAsync);
    int before = starts;
    await Task.WhenAll(requests);
    int first = starts;
    await Task.WhenAll(requests);
    return (before, first, starts);
}
```

- A. (0, 3, 3)；IEnumerable<Task<int>> 自动缓存已创建的 Task。
- B. (0, 3, 6)；把 Select 的结果 ToArray 一次，再重复使用该数组。
- C. (3, 3, 3)；Select 声明时就已调用全部 FetchAsync。
- D. (0, 0, 0)；Task.FromResult 不算调用 FetchAsync。
