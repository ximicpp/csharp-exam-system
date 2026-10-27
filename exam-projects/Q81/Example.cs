// Q201 · await 已完成的 Task（考试第 81 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static async Task<int> Answer201() => await Task.FromResult(5) + 1;

    private static async Task<string> Q201()
    {
        Task<int> result = Answer201();
        return $"{result.IsCompletedSuccessfully},{await result}";
    }
}
