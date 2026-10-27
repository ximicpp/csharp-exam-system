// Q168 · override 内的 base 调用（考试第 48 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private class Base168
    {
        public virtual string Name() => "base";
    }
    private sealed class Derived168 : Base168
    {
        public override string Name() => base.Name() + "+derived";
    }

    private static string Q168()
    {
        Base168 value = new Derived168();
        return value.Name();
    }
}
