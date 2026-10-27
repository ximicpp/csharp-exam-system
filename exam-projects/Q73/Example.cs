// Q193 · 展平查询与外侧标签（考试第 73 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q193()
    {
        var projects = new[] { (Name: "p", Items: new[] { "a", "b" }), (Name: "q", Items: new[] { "c" }) };
        var rows = projects.SelectMany(project => project.Items, (project, item) => $"{project.Name}:{item}");
        return string.Join(",", rows);
    }
}
