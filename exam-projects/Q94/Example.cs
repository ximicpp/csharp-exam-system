// Q214 · 表达式树与捕获变量（考试第 94 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q214()
    {
        int limit = 3;
        Expression<Func<int, bool>> rule = value => value > limit;
        Func<int, bool> compiled = rule.Compile();
        limit = 8;
        return $"{rule.Body.NodeType},{compiled(5)}";
    }
}
