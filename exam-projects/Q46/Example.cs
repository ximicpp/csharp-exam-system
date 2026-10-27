// Q166 · record struct 的 with 更新（考试第 46 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private record struct Point166(int X, int Y);

    private static string Q166()
    {
        Point166 start = new(2, 3);
        Point166 moved = start with { X = 7 };
        return $"{start.X},{start.Y}|{moved.X},{moved.Y}";
    }
}
