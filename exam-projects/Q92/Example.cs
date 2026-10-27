// Q212 · 封闭泛型类型与泛型定义（考试第 92 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q212()
    {
        Type closed = typeof(List<int>);
        Type definition = closed.GetGenericTypeDefinition();
        return $"{closed.IsGenericType},{definition == typeof(List<>)},{closed == definition}";
    }
}
