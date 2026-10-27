// Q42 · object 中保存的是可变值的哪一份（考试第 132 题）
using System.Collections.Concurrent;

internal static partial class Question
{
    private struct Position
    {
        public int X;
    }
    private static (int Original, int Boxed, int Unboxed) BoxingSnapshot()
    {
        var original = new Position { X = 3 };
        object boxed = original;
        original.X = 9;
        Position unboxed = (Position)boxed;
        unboxed.X = 7;
        return (original.X, ((Position)boxed).X, unboxed.X);
    }
}
