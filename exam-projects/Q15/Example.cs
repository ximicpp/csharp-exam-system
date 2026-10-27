// Q135 · 新数组里的初始元素（考试第 15 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q135()
    {
        int[] counts = new int[2];
        string?[] names = new string?[2];
        return $"{counts[0]},{names[0] is null},{counts.Length}";
    }
}
