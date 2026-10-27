// Q170 · 接口属性与实现类（考试第 50 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private interface IIdentified170 { int Id { get; } }
    private sealed class Entity170 : IIdentified170
    {
        public int Id { get; init; }
        public string Name { get; init; } = "";
    }

    private static string Q170()
    {
        IIdentified170 item = new Entity170 { Id = 6, Name = "job" };
        return item.Id.ToString(CultureInfo.InvariantCulture);
    }
}
