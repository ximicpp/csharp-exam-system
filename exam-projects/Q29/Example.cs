// Q149 · do 与 while 的执行次数（考试第 29 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q149()
    {
        int first = 0;
        int second = 0;
        do { first++; } while (first < 0);
        while (second < 0) { second++; }
        return $"{first},{second}";
    }
}
