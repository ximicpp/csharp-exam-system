await Question.Run();

internal static partial class Question
{
    internal static async Task Run()
    {
        var ledger = new Ledger();
        await Task.WhenAll(Enumerable.Range(0, 4).Select(worker => Task.Run(() =>
        {
            for (int i = 0; i < 500; i++)
            {
                ledger.DepositOne();
                _ = ledger.Snapshot();
            }
        })));
        Console.WriteLine(ledger.Snapshot());
    }
}
