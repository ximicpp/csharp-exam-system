// Q162 · 私有 setter 与类内状态更新（考试第 42 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private sealed class Counter162
    {
        public int Count { get; private set; }
        public void Increment() => Count++;
    }

    private static string Q162()
    {
        Counter162 counter = new();
        counter.Increment();
        counter.Increment();
        return counter.Count.ToString(CultureInfo.InvariantCulture);
    }
}
