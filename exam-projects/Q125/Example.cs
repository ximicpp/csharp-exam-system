// Q08 · 可变哈希键会破坏什么（考试第 125 题）

internal static partial class Question
{
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

    private static void Observe()
    {
        Dictionary<CacheKey, string> cache = BuildCache();
        Console.WriteLine($"entries={cache.Count}");
        foreach (KeyValuePair<CacheKey, string> entry in cache)
            Console.WriteLine($"stored key.Name={entry.Key.Name}, value={entry.Value}");

        var originalName = new CacheKey { Name = "before" };
        var newName = new CacheKey { Name = "after" };
        Console.WriteLine($"lookup.Name={originalName.Name}, found={cache.ContainsKey(originalName)}");
        Console.WriteLine($"lookup.Name={newName.Name}, found={cache.ContainsKey(newName)}");
    }
}
