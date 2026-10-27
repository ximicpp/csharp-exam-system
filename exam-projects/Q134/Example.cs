// Q44 · Span 与 ReadOnlySpan 的数据关系（考试第 134 题）
using System.Collections.Concurrent;

internal static partial class Question
{
    private static (int ReadOnlyFirst, int TailValue) SharedViews()
    {
        int[] data = [10, 20, 30];
        Span<int> middle = data.AsSpan(1, 2);
        ReadOnlySpan<int> readOnly = middle;
        middle[0] = 99;
        data[2] = 7;
        return (readOnly[0], middle[1]);
    }
}
