using System.Globalization;

var suite = new QuizSuite();
QuizTypes.Register(suite);
QuizExecution.Register(suite);
QuizRuntime.Register(suite);
QuizFoundations.Register(suite);
QuizModeling.Register(suite);
QuizQueries.Register(suite);
QuizMicrosoft.Register(suite);
if (args is ["--list"])
{
    Console.WriteLine(string.Join('\n', suite.Ids));
    return 0;
}
if (args.Length == 0 || args is ["--all"])
    return await suite.RunAsync(suite.Ids);
if (args.All(suite.Contains))
    return await suite.RunAsync(args.Distinct(StringComparer.Ordinal));
Console.Error.WriteLine("Usage: Quiz.Checks [--all | --list | Q01 Q02 ...]");
return 2;

internal sealed class QuizSuite
{
    private readonly SortedDictionary<string, Func<Task>> checks = new(StringComparer.Ordinal);
    internal IEnumerable<string> Ids => checks.Keys.OrderBy(id => int.Parse(id.AsSpan(1), CultureInfo.InvariantCulture));
    internal bool Contains(string id) => checks.ContainsKey(id);

    internal void Add(string id, Action check) => AddAsync(id, () =>
    {
        check();
        return Task.CompletedTask;
    });

    internal void AddAsync(string id, Func<Task> check) => checks.Add(id, check);

    internal async Task<int> RunAsync(IEnumerable<string> ids)
    {
        int count = 0;
        foreach (string id in ids)
        {
            try
            {
                // A watchdog for broken checks, never evidence of scheduling semantics.
                await checks[id]().WaitAsync(TimeSpan.FromSeconds(30));
                Console.WriteLine($"PASS: {id}");
                count++;
            }
            catch (Exception error)
            {
                Console.Error.WriteLine($"FAIL: {id}: {error}");
                return 1;
            }
        }
        Console.WriteLine($"PASS: quiz runtime checks ({count}/{count})");
        return 0;
    }
}

internal static class QuizAssert
{
    internal static void True(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    internal static void Equal<T>(T expected, T actual)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
            throw new InvalidOperationException($"Expected <{expected}>, got <{actual}>");
    }

    internal static TException Throws<TException>(Action action) where TException : Exception
    {
        try { action(); }
        catch (TException error) { return error; }
        throw new InvalidOperationException($"Expected {typeof(TException).Name}");
    }

    internal static async Task<TException> ThrowsAsync<TException>(Func<Task> action)
        where TException : Exception
    {
        try { await action(); }
        catch (TException error) { return error; }
        throw new InvalidOperationException($"Expected {typeof(TException).Name}");
    }

    internal static string Capture(Action action)
    {
        TextWriter original = Console.Out;
        using var output = new StringWriter(CultureInfo.InvariantCulture);
        try
        {
            Console.SetOut(output);
            action();
            return output.ToString().Replace("\r\n", "\n", StringComparison.Ordinal).TrimEnd('\n');
        }
        finally { Console.SetOut(original); }
    }
}
