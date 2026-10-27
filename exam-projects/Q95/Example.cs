// Q215 · dynamic 的成员绑定（考试第 95 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q215()
    {
        dynamic text = "hello";
        try { _ = text.MissingMember(); }
        catch (Microsoft.CSharp.RuntimeBinder.RuntimeBinderException) { return "binding failed"; }
        return "success";
    }
}
