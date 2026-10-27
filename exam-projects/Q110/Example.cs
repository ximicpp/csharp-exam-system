// Q230 · XML 文档注释与参数校验（考试第 110 题）

internal static partial class Question
{
    /// <summary>返回传入的数值。</summary>
    /// <param name="value">正数。</param>
    private static int Documented(int value) => value;
    private static int Checked(int value)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(value);
        return value;
    }
    private static int Observe() => Documented(-1);

}
