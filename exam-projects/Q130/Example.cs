// Q14 · 显式接口实现可以改变调用入口（考试第 130 题）
using System.Globalization;
using System.Numerics;
using System.Text;

internal static partial class Question
{
    private interface IFormatter
    {
        string Format();
    }

    private sealed class Formatter : IFormatter
    {
        public string Format() => "public";
        string IFormatter.Format() => "interface";
    }

    private static (string Concrete, string Interface, bool SameObject) ExplicitCall()
    {
        var formatter = new Formatter();
        IFormatter view = formatter;
        return (formatter.Format(), view.Format(), ReferenceEquals(formatter, view));
    }
}
