// Q173 · 序列接口的协变（考试第 53 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private class Animal173 { }
    private sealed class Cat173 : Animal173 { }

    private static string Q173()
    {
        IEnumerable<Cat173> cats = new List<Cat173> { new() };
        IEnumerable<Animal173> animals = cats;
        return animals.Single().GetType().Name;
    }
}
