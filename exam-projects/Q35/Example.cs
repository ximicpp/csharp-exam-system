// Q155 · 解构赋值与弃元（考试第 35 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q155()
    {
        int count = 9;
        (string status, _) = ("ready", 3);
        return $"{status},{count}";
    }
}
