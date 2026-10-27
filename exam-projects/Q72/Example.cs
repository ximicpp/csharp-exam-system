// Q192 · 查询 let 与中间计算（考试第 72 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q192()
    {
        int calls = 0;
        int Square(int value) { calls++; return value * value; }
        int[] source = [2, 3];
        var query = from value in source let square = Square(value) where square > 4 select square;
        string result = string.Join(",", query);
        return $"{result}|{calls}";
    }
}
