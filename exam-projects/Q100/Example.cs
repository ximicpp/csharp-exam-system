// Q220 · unsafe、指针与 GC（考试第 100 题）

internal static partial class Question
{
    private static unsafe int Observe()
    {
        int[] values = [1, 2];
        fixed (int* address = values) { address[0] = 7; }
        return values[0];
    }

}
