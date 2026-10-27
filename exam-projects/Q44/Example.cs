// Q164 · 静态字段与实例状态（考试第 44 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private sealed class Ticket164
    {
        public static int Created;
        public int Id { get; } = ++Created;
    }

    private static string Q164()
    {
        Ticket164.Created = 0;
        Ticket164 first = new();
        Ticket164 second = new();
        return $"{first.Id},{second.Id},{Ticket164.Created}";
    }
}
