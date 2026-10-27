// Q204 · async 方法的异常传播（考试第 84 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static async Task<int> Fail204()
    {
        int value = int.Parse("bad", CultureInfo.InvariantCulture);
        await Task.CompletedTask;
        return value;
    }

    private static async Task<string> Q204()
    {
        Task<int> task = Fail204();
        try { _ = await task; }
        catch (FormatException) { return $"{task.IsFaulted},caught"; }
        return "success";
    }
}
