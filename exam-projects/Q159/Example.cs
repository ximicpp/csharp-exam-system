// Q37 · async void 应放在哪个边界（考试第 159 题）

internal static partial class Question
{
    private static async Task SaveAsync(bool fail)
    {
        await Task.Yield();
        if (fail) throw new InvalidOperationException("save failed");
    }
    private static async Task<(bool BatchCaught, bool EventCaught)> Observe()
    {
        bool batchCaught = false;
        try { await SaveAsync(true); }
        catch (InvalidOperationException) { batchCaught = true; }
        var completed = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
        async void ButtonClicked()
        {
            try { await SaveAsync(true); completed.SetResult(false); }
            catch (InvalidOperationException) { completed.SetResult(true); }
        }
        ButtonClicked();
        return (batchCaught, await completed.Task);
    }

}
