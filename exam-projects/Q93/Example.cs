// Q213 · 通过反射读取特性（考试第 93 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    [AttributeUsage(AttributeTargets.Class)]
    private sealed class Priority213Attribute(int value) : Attribute
    {
        public int Value { get; } = value;
    }
    [Priority213(4)]
    private sealed class Job213 { }

    private static string Q213()
    {
        var attribute = typeof(Job213).GetCustomAttribute<Priority213Attribute>();
        return attribute?.Value.ToString(CultureInfo.InvariantCulture) ?? "missing";
    }
}
