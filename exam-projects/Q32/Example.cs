// Q152 · ref 参数与调用方变量（考试第 32 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q152()
    {
        static void Advance(ref int position) => position += 2;
        int cursor = 3;
        Advance(ref cursor);
        return cursor.ToString(CultureInfo.InvariantCulture);
    }
}
