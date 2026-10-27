// Q175 · 排序比较器与顺序（考试第 55 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q175()
    {
        int[] values = [2, 8, 5];
        Array.Sort(values, Comparer<int>.Create((left, right) => right.CompareTo(left)));
        return string.Join(",", values);
    }
}
