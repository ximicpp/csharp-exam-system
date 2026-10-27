// Q225 · readonly 字段的初始化（考试第 105 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private sealed class Token225
    {
        public readonly int Id;
        public Token225(int id) => Id = id;
    }

    private static string Q225()
    {
        Token225 value = new(7);
        return value.Id.ToString(CultureInfo.InvariantCulture);
    }
}
