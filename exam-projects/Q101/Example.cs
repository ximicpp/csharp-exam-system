// Q221 · 结构体复制与数值字段（考试第 101 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private struct Position221 { public int X; }

    private static string Q221()
    {
        Position221 start = new() { X = 3 };
        Position221 copy = start;
        copy.X = 8;
        return $"{start.X},{copy.X}";
    }
}
