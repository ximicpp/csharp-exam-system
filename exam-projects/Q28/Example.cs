// Q148 · 跳过一项与终止循环（考试第 28 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q148()
    {
        int total = 0;
        foreach (int value in new[] { 3, -2, 4, 0, 9 })
        {
            if (value < 0) continue;
            if (value == 0) break;
            total += value;
        }
        return total.ToString(CultureInfo.InvariantCulture);
    }
}
