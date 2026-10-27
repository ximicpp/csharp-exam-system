// Q223 · default 与显式结构构造器（考试第 103 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private struct Options223
    {
        public int Limit;
        public Options223() => Limit = 5;
    }

    private static string Q223()
    {
        Options223 constructed = new();
        Options223 zeroed = default;
        return $"{constructed.Limit},{zeroed.Limit}";
    }
}
