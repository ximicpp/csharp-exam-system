// Q52 · 泛型代码共享会合并静态状态吗（考试第 140 题）
using System.Collections.Concurrent;

internal static partial class Question
{
    private static class Cache<T>
    {
        public static int Hits;
    }
    private static (int StringHits, int ObjectHits, bool SameType) GenericState()
    {
        Cache<string>.Hits = 7;
        Cache<object>.Hits = 0;
        return (Cache<string>.Hits, Cache<object>.Hits,
            typeof(Cache<string>) == typeof(Cache<object>));
    }
}
