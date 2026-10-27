#region Q79
Console.WriteLine(Classify(""));

static string Classify(string? value) => value switch
{
    string => "text",
    string { Length: 0 } => "empty",
    null => "missing"
};
#endregion
