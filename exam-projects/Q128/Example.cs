// Q12 · var、object 与 dynamic 的绑定时机（考试第 128 题）
using System.Globalization;
using System.Numerics;
using System.Text;

internal static partial class Question
{
    private static string Describe(string value) => "string";
    private static string Describe(object value) => "object";

    private static (string Inferred, string Object, string Dynamic) BindOverloads()
    {
        var inferred = "hello";
        object boxedView = inferred;
        dynamic dynamicView = inferred;
        return (Describe(inferred), Describe(boxedView), Describe(dynamicView));
    }
}
