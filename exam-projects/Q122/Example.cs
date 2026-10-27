// Q02 · 值类型中的引用字段（考试第 122 题）
using System.Globalization;
using System.Numerics;
using System.Text;

internal static partial class Question
{
    private struct Envelope
    {
        public int Version;
        public List<string> Tags;
    }

    private static (int AVersion, int BVersion, int ATags, int BTags) CopyEnvelope()
    {
        var a = new Envelope { Version = 1, Tags = ["draft"] };
        var b = a;
        b.Version = 8;
        b.Tags.Add("reviewed");
        return (a.Version, b.Version, a.Tags.Count, b.Tags.Count);
    }
}
