// Q125 · 缩窄转换是否检测溢出（考试第 5 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q125()
    {
        int value = 300;
        byte wrapped = unchecked((byte)value);
        try { _ = checked((byte)value); }
        catch (OverflowException) { return $"{wrapped},overflow"; }
        return "no-error";
    }
}
