// Q185 · 异常过滤器与后续 catch（考试第 65 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q185()
    {
        List<string> log = [];
        bool Accept() { log.Add("filter"); return false; }
        try { throw new InvalidOperationException(); }
        catch (InvalidOperationException) when (Accept()) { log.Add("first"); }
        catch (InvalidOperationException) { log.Add("fallback"); }
        return string.Join(",", log);
    }
}
