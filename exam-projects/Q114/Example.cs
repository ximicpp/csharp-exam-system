// Q234 · 泛型数学的运算约束（考试第 114 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static T Add234<T>(T left, T right) where T : System.Numerics.INumber<T>
        => left + right;

    private static string Q234()
    {
        return Add234(1.5m, 2.5m).ToString("F1", CultureInfo.InvariantCulture);
    }
}
