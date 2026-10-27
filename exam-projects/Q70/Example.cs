// Q190 · using 的空资源处理（考试第 70 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q190()
    {
        IDisposable? optional = null;
        int calls = 0;
        using (optional) { calls++; }
        return calls.ToString(CultureInfo.InvariantCulture);
    }
}
