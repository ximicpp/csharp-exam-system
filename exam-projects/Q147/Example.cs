// Q87 · public const 的发布边界（考试第 147 题）

internal static partial class Question
{
    private static class Library
    {
        public const int Limit = 10;
        public static readonly int RuntimeLimit = 10;
    }
    private static int Client() => Library.Limit;
    private static (int ConstantValue, int ReadonlyValue) Observe() => (Client(), Library.RuntimeLimit);

}
