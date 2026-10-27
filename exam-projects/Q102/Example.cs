// Q222 · 类变量赋值与对象状态（考试第 102 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private sealed class Box222 { public int Value; }

    private static string Q222()
    {
        Box222 first = new() { Value = 3 };
        Box222 second = first;
        second.Value = 8;
        return $"{first.Value},{ReferenceEquals(first, second)}";
    }
}
