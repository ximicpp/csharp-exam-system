// Q205 · 取消令牌与检查点（考试第 85 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q205()
    {
        CancellationToken token = new(canceled: true);
        try { token.ThrowIfCancellationRequested(); }
        catch (OperationCanceledException error) { return $"{error.CancellationToken == token},canceled"; }
        return "continued";
    }
}
