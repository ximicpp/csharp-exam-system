// Q140 · 集合重复插入的返回值（考试第 20 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q140()
    {
        HashSet<int> seen = [5];
        bool first = seen.Add(8);
        bool duplicate = seen.Add(5);
        return $"{first},{duplicate},{seen.Count}";
    }
}
