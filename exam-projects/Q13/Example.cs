// Q133 · 字符单元与 Unicode 标量（考试第 13 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q133()
    {
        string text = "A\U0001F600";
        int scalars = 0;
        foreach (Rune rune in text.EnumerateRunes()) scalars++;
        return $"{text.Length},{scalars}";
    }
}
