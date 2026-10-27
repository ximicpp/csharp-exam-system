// Q126 · 十进制字面量的计算（考试第 6 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q126()
    {
        decimal amount = 0.1m + 0.2m;
        return amount.ToString(CultureInfo.InvariantCulture);
    }
}
