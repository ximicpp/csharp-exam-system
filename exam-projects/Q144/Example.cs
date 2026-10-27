// Q60 · in 参数与结构体成员调用（考试第 144 题）
using System.Collections.Concurrent;

internal static partial class Question
{
    private struct Cursor
    {
        public int Position;
        public int Advance() => ++Position;
    }

    private static (int First, int Second) Probe(in Cursor cursor)
        => (cursor.Advance(), cursor.Advance());
    private static (int First, int Second, int Original) ReadonlyCopies()
    {
        var cursor = new Cursor();
        var pair = Probe(in cursor);
        return (pair.First, pair.Second, cursor.Position);
    }
}
