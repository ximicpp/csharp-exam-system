// Q184 · 参数异常的参数名（考试第 64 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q184()
    {
        static void Validate(int size)
        {
            if (size <= 0) throw new ArgumentOutOfRangeException(nameof(size));
        }
        try { Validate(0); }
        catch (ArgumentOutOfRangeException error) { return error.ParamName ?? "missing"; }
        return "accepted";
    }
}
