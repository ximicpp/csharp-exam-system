// Q229 · 自定义运算符的调用（考试第 109 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private readonly record struct Distance229(int Meters)
    {
        public static Distance229 operator +(Distance229 left, Distance229 right) => new(left.Meters + right.Meters);
    }

    private static string Q229()
    {
        Distance229 first = new(3);
        Distance229 second = new(4);
        return (first + second).Meters.ToString(CultureInfo.InvariantCulture);
    }
}
