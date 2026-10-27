// Q154 · 局部函数的声明与调用（考试第 34 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q154()
    {
        int result = Factorial(4);
        return result.ToString(CultureInfo.InvariantCulture);

        static int Factorial(int n) => n <= 1 ? 1 : n * Factorial(n - 1);
    }
}
