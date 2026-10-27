// Q228 · 自定义索引器的访问（考试第 108 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private sealed class Slots228
    {
        private readonly int[] data = new int[2];
        public int this[int index] { get => data[index]; set => data[index] = value; }
    }

    private static string Q228()
    {
        Slots228 slots = new();
        slots[1] = 9;
        return $"{slots[0]},{slots[1]}";
    }
}
