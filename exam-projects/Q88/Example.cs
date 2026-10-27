// Q208 · SemaphoreSlim 的许可与等待（考试第 88 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static async Task<string> Q208()
    {
        using SemaphoreSlim gate = new(1, 1);
        await gate.WaitAsync();
        Task next = gate.WaitAsync();
        bool waiting = !next.IsCompleted;
        gate.Release();
        await next;
        int available = gate.CurrentCount;
        gate.Release();
        return $"{waiting},{available}";
    }
}
