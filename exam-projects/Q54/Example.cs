// Q174 · 回调参数的逆变（考试第 54 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q174()
    {
        string log = "";
        Action<object> record = value => log = value.GetType().Name;
        Action<string> acceptText = record;
        acceptText("hello");
        return log;
    }
}
