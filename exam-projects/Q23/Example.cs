// Q143 · null 条件索引会不会计算索引（考试第 23 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q143()
    {
        int calls = 0;
        int Index() { calls++; return 0; }
        int[]? data = null;
        int value = data?[Index()] ?? 9;
        return $"{value},{calls}";
    }
}
