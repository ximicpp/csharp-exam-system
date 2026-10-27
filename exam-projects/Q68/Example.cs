// Q188 · 异步释放的故障传播（考试第 68 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private sealed class Resource188 : IAsyncDisposable
    {
        public ValueTask DisposeAsync() => ValueTask.FromException(new InvalidOperationException("dispose failed"));
    }

    private static async Task<string> Q188()
    {
        try
        {
            await using var resource = new Resource188();
        }
        catch (InvalidOperationException error) { return error.Message; }
        return "success";
    }
}
