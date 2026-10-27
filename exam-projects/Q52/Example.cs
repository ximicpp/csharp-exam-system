// Q172 · 泛型约束与比较操作（考试第 52 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static T Smaller172<T>(T left, T right) where T : IComparable<T>
        => left.CompareTo(right) <= 0 ? left : right;

    private static string Q172()
    {
        return Smaller172(8, 3).ToString(CultureInfo.InvariantCulture);
    }
}
