// Q237 · Release 下的条件编译（考试第 117 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q237()
    {
        #if DEBUG
        return "debug";
        #else
        return "release";
        #endif
    }
}
