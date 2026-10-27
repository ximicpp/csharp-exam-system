// Q137 · Remove 删除哪一个重复项（考试第 17 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q137()
    {
        List<int> pending = [4, 7, 4];
        bool removed = pending.Remove(4);
        return $"{removed}:{string.Join(",", pending)}";
    }
}
