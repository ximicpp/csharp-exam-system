// Q145 · when 条件与匹配顺序（考试第 25 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q145()
    {
        static string Classify(int count) => count switch
        {
            int n when n >= 0 => "nonnegative",
            int n when n > 10 => "large",
            _ => "negative"
        };
        return Classify(20);
    }
}
