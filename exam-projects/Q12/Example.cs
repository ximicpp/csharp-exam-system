// Q132 · 插值中的宽度与数字格式（考试第 12 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q132()
    {
        int id = 7;
        double score = 2.5;
        return string.Create(CultureInfo.InvariantCulture, $"[{id,5:D3}]/{score:F1}");
    }
}
