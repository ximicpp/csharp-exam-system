// Q138 · 字典中的零与缺失键（考试第 18 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q138()
    {
        Dictionary<string, int> config = new() { ["retry"] = 0 };
        bool found = config.TryGetValue("retry", out int retry);
        bool missing = config.TryGetValue("timeout", out int timeout);
        return $"{found},{retry},{missing},{timeout}";
    }
}
