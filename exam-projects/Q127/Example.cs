// Q11 · 回调参数中变型的安全方向（考试第 127 题）

internal static partial class Question
{
    private static int Observe()
    {
        int count = 0;
        Action<IEnumerable<object>> wider = values => count = values.Count();
        Action<IEnumerable<string>> callback = wider;
        callback(new[] { "a", "b" });
        return count;
    }

}
