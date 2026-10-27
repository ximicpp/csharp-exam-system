// Q156 · 字面量选择哪一个重载（考试第 36 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Tag156(int value) => "int";
    private static string Tag156(double value) => "double";
    private static string Tag156(decimal value) => "decimal";

    private static string Q156()
    {
        return $"{Tag156(1)}|{Tag156(1.0)}|{Tag156(1.0m)}";
    }
}
