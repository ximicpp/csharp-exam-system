// Q153 · TryParse 失败时的输出（考试第 33 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q153()
    {
        int value = 17;
        bool ok = int.TryParse("not-a-number", NumberStyles.Integer, CultureInfo.InvariantCulture, out value);
        return $"{ok},{value}";
    }
}
