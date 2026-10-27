// Q41 · 把 class 改成 struct 就能摆脱 GC 吗（考试第 131 题）

internal static partial class Question
{
    private struct Item { public int Number; public string Name; }
    private static (int Original, int Copy, bool SharedString) Observe()
    {
        string name = new(['a', 'b']);
        Item[] items = [new Item { Number = 1, Name = name }];
        Item copy = items[0];
        copy.Number = 7;
        return (items[0].Number, copy.Number, ReferenceEquals(items[0].Name, copy.Name));
    }

}
