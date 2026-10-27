// Q227 · 从末尾索引与范围右端（考试第 107 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q227()
    {
        int[] values = [1, 2, 3, 4];
        int last = values[^1];
        int[] middle = values[1..^1];
        return $"{last}|{string.Join(",", middle)}";
    }
}
