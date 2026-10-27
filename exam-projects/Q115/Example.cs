// Q235 · 同一线程的嵌套 lock（考试第 115 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q235()
    {
        object gate = new();
        int count = 0;
        lock (gate) { count++; lock (gate) { count++; } }
        return count.ToString(CultureInfo.InvariantCulture);
    }
}
