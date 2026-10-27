// Q06 · record 的相等性与复制深度（考试第 124 题）
using System.Globalization;
using System.Numerics;
using System.Text;

internal static partial class Question
{
    private sealed record Report(string Name, List<string> Tags);

    private static (bool IndependentEqual, bool CopyEqual, bool SameReport, int OriginalTags) CopyRecord()
    {
        var original = new Report("daily", ["draft"]);
        var independent = new Report("daily", ["draft"]);
        var copy = original with { };
        copy.Tags.Add("reviewed");
        return (original == independent, original == copy,
            ReferenceEquals(original, copy), original.Tags.Count);
    }
}
