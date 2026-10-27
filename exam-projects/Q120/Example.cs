// Q240 · Native AOT 的动态能力边界（考试第 120 题）

internal static partial class Question
{
    private static (bool DynamicCode, int Result) Observe()
    {
        var expression = System.Linq.Expressions.Expression.Lambda<Func<int>>(
            System.Linq.Expressions.Expression.Constant(42));
        return (System.Runtime.CompilerServices.RuntimeFeature.IsDynamicCodeSupported, expression.Compile()());
    }

}
