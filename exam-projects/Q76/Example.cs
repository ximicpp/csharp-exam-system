// Q196 · 排序键相同时的元素顺序（考试第 76 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q196()
    {
        var tasks = new[] { (Name: "b", Priority: 1), (Name: "a", Priority: 1), (Name: "c", Priority: 0) };
        return string.Join(",", tasks.OrderBy(task => task.Priority).Select(task => task.Name));
    }
}
