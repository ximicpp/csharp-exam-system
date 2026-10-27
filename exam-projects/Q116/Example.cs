// Q236 · CPU 工作与异步 I/O 的选择（考试第 116 题）

internal static partial class Question
{
    private static async Task<int> ExistingIoApi(Task<int> input) => await input;
    private static int CpuParse(int input) => input * input;
    private static async Task<(bool Pending, int Io, int Cpu)> Observe()
    {
        var source = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
        Task<int> io = ExistingIoApi(source.Task);
        bool pending = !io.IsCompleted;
        source.SetResult(7);
        int cpu = await Task.Run(() => CpuParse(3));
        return (pending, await io, cpu);
    }

}
