// Q90 · 默认接口实现的调用视图（考试第 150 题）


internal static partial class Question
{
    private interface ILabel
    {
        string Label() => "default";
    }
    private sealed class Labelled : ILabel { }
    private static (string Label, bool ClassHasNoMethod) DefaultInterface()
    {
        ILabel item = new Labelled();
        return (item.Label(), typeof(Labelled).GetMethod("Label") is null);
    }
}
