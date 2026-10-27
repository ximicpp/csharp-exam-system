#region Q61
sealed class Options
{
    public string Path { get; } = "input.jsonl";
}

var options = new Options();
Console.WriteLine(options.Path);
#endregion
