// Q89 · 命名实参的求值顺序（考试第 149 题）


internal static partial class Question
{
    private static (int First, int Second, string Trace) NamedEvaluation()
    {
        var trace = new List<string>();
        int Next(string label) { trace.Add(label); return trace.Count; }
        static (int, int) Pair(int first, int second) => (first, second);
        var pair = Pair(second: Next("B"), first: Next("A"));
        return (pair.Item1, pair.Item2, string.Join(',', trace));
    }
}
