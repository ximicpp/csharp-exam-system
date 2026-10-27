// Q186 · using 声明的释放边界（考试第 66 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private sealed class Resource186(List<string> log) : IDisposable
    {
        public void Dispose() => log.Add("dispose");
    }

    private static string Q186()
    {
        List<string> log = [];
        {
            using var resource = new Resource186(log);
            log.Add("body");
            log.Add("tail");
        }
        log.Add("outer");
        return string.Join(",", log);
    }
}
