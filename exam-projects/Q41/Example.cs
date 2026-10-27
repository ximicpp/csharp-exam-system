// Q161 · 把参数交给基类构造函数（考试第 41 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private class Store161
    {
        public int Capacity { get; }
        public Store161(int capacity) => Capacity = capacity;
    }
    private sealed class Worker161 : Store161
    {
        public Worker161(int seed) : base(seed + 1) { }
    }

    private static string Q161()
    {
        Worker161 worker = new(3);
        return worker.Capacity.ToString(CultureInfo.InvariantCulture);
    }
}
