// Q217 · field 支持的属性规范化（考试第 97 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private sealed class Label217
    {
        public string Text { get; set => field = value.Trim(); } = "";
    }

    private static string Q217()
    {
        Label217 label = new() { Text = "  go  " };
        return $"[{label.Text}]";
    }
}
