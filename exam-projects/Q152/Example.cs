// Q98 · 多播委托的返回值（考试第 152 题）


internal static partial class Question
{
    private static (int Result, string Trace) InvokeDelegates()
    {
        var trace = new List<string>();
        Func<int> handler = () => { trace.Add("first"); return 5; };
        handler += () => { trace.Add("second"); return 10; };
        return (handler(), string.Join(',', trace));
    }
}
