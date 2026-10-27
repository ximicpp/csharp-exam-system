// Q163 · 对象初始化器与构造函数（考试第 43 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private sealed class Settings163
    {
        public int Level { get; set; }
        public Settings163() => Level = 3;
    }

    private static string Q163()
    {
        Settings163 options = new() { Level = 8 };
        return options.Level.ToString(CultureInfo.InvariantCulture);
    }
}
