// Q195 · 左外连接与未匹配项（考试第 75 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q195()
    {
        int[] orders = [1, 2];
        var customers = new[] { (Id: 1, Name: "Lin") };
        var rows = from id in orders
                   join customer in customers on id equals customer.Id into matches
                   from customer in matches.DefaultIfEmpty()
                   select $"{id}:{customer.Name ?? "missing"}";
        return string.Join(",", rows);
    }
}
