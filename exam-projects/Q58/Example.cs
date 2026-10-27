// Q178 · 多播调用遇到异常（考试第 58 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q178()
    {
        List<string> log = [];
        Action handlers = () => log.Add("first");
        handlers += () => throw new InvalidOperationException("broken");
        handlers += () => log.Add("last");
        try { handlers(); }
        catch (InvalidOperationException) { log.Add("caught"); }
        return string.Join(",", log);
    }
}
