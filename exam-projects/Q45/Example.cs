// Q165 · 记录相等与普通类相等（考试第 45 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private sealed record Person165(string Name);
    private sealed class Plain165(string name)
    {
        public string Name { get; } = name;
    }

    private static string Q165()
    {
        Person165 a = new("Lin");
        Person165 b = new("Lin");
        Plain165 x = new("Lin");
        Plain165 y = new("Lin");
        return $"{a == b},{x == y}";
    }
}
