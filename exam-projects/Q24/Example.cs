// Q144 · 布尔异或的结果（考试第 24 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q144()
    {
        bool a = true;
        bool b = true;
        return $"{a ^ b},{a ^ false},{!a}";
    }
}
