// Q197 · 分页的跳过与取出数量（考试第 77 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q197()
    {
        int[] items = [10, 20, 30, 40, 50];
        return string.Join(",", items.Skip(2).Take(2));
    }
}
