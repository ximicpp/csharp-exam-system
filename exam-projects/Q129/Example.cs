// Q13 · override 与 new 的调用分派（考试第 129 题）
using System.Globalization;
using System.Numerics;
using System.Text;

internal static partial class Question
{
    private class Writer
    {
        public virtual string Format() => "base";
        public string Label() => "base";
    }

    private sealed class JsonWriter : Writer
    {
        public override string Format() => "derived";
        public new string Label() => "derived";
    }

    private static (string Virtual, string BaseView, string DerivedView) DispatchMembers()
    {
        Writer writer = new JsonWriter();
        return (writer.Format(), writer.Label(), ((JsonWriter)writer).Label());
    }
}
