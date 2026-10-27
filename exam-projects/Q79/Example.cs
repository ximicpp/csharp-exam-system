// Q199 · ToLookup 与同键多项（考试第 79 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q199()
    {
        var entries = new[] { (User: "u", Value: 2), (User: "u", Value: 3) };
        var lookup = entries.ToLookup(row => row.User, row => row.Value);
        return $"{string.Join(",", lookup["u"])}|{lookup["absent"].Count()}";
    }
}
