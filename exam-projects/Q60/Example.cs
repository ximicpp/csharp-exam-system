// Q180 · 泛型方法的类型推断（考试第 60 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static T Identity180<T>(T value) => value;

    private static string Q180()
    {
        var number = Identity180(3);
        var text = Identity180("three");
        return $"{number.GetType().Name},{text.GetType().Name}";
    }
}
