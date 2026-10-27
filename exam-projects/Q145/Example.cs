// Q81 · 构造函数体的先后（考试第 145 题）


internal static partial class Question
{
    private class Parent
    {
        public Parent(List<string> trace) => trace.Add("base");
    }
    private sealed class Child : Parent
    {
        public Child(List<string> trace) : base(trace) => trace.Add("derived");
    }
    private static string ConstructorOrder()
    {
        var trace = new List<string>();
        _ = new Child(trace);
        return string.Join(',', trace);
    }
}
