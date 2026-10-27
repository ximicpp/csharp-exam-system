#region Q171
Console.WriteLine(Create<NeedsArg>().Value);
static T Create<T>() where T : new() => new T();
class NeedsArg
{
    public int Value { get; }
    public NeedsArg(int value) => Value = value;
}
#endregion
