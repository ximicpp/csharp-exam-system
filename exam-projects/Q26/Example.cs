// Q146 · 列表模式与元素数量（考试第 26 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q146()
    {
        static bool Valid(string[] args) => args is ["--limit", _];
        return $"{Valid(["--limit", "5"])},{Valid(["--limit", "5", "extra"])}";
    }
}
