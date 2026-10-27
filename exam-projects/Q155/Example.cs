// Q30 · IQueryable 的表达式在哪里执行（考试第 155 题）

internal static partial class Question
{
    private static (int Before, int Calls, string Items) Observe()
    {
        int calls = 0;
        string Normalize(string value) { calls++; return value.Trim().ToUpperInvariant(); }
        IQueryable<string> upstream = new[] { " a ", "b", " c " }.AsQueryable().Where(s => s.Length > 0);
        IEnumerable<string> local = upstream.AsEnumerable().Where(s => Normalize(s) != "B");
        int before = calls;
        string items = string.Join(',', local.Select(s => s.Trim().ToUpperInvariant()));
        return (before, calls, items);
    }

}
