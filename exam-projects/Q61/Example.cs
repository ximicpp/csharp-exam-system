// Q181 · catch 与 finally 的执行顺序（考试第 61 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q181()
    {
        List<string> log = [];
        try { log.Add("try"); throw new FormatException(); }
        catch (FormatException) { log.Add("catch"); }
        finally { log.Add("finally"); }
        log.Add("after");
        return string.Join(",", log);
    }
}
