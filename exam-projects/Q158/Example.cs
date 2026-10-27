// Q36 · 任务查询的重复枚举（考试第 158 题）


internal static partial class Question
{
    private static async Task<(int Before, int First, int Second)> Q36()
    {
        int starts = 0;
        Task<int> FetchAsync(int id)
        {
            starts++;
            return Task.FromResult(id);
        }
        int[] ids = [1, 2, 3];
        IEnumerable<Task<int>> requests = ids.Select(FetchAsync);
        int before = starts;
        await Task.WhenAll(requests);
        int first = starts;
        await Task.WhenAll(requests);
        return (before, first, starts);
    }
}
