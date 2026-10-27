// Q141 · ??= 何时计算后备值（考试第 21 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q141()
    {
        int calls = 0;
        string Fallback() { calls++; return "guest"; }
        string? name = null;
        name ??= Fallback();
        name ??= Fallback();
        return $"{name},{calls}";
    }
}
