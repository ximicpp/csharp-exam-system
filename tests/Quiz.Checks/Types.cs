using System.Globalization;
using System.Numerics;
using System.Text;

internal static class QuizTypes
{
    internal static void Register(QuizSuite suite)
    {
        suite.Add("Q01", () => QuizAssert.Equal((2, 3), PassReferences()));
        suite.Add("Q02", () => QuizAssert.Equal((1, 8, 2, 2), CopyEnvelope()));
        suite.Add("Q04", () => QuizAssert.Equal(("ready", true, true), DefaultSettings()));
        suite.Add("Q05", () => QuizAssert.Throws<NullReferenceException>(() => NullSuppression()));
        suite.Add("Q06", () => QuizAssert.Equal((false, true, false, 2), CopyRecord()));
        suite.Add("Q07", () => QuizAssert.Equal((true, 2), InitializeRequest()));
        suite.Add("Q10", () =>
        {
            QuizAssert.Equal(6, SumNumbers<int>([1, 2, 3]));
            QuizAssert.Equal(0.3m, SumNumbers<decimal>([0.1m, 0.2m]));
            QuizAssert.Equal(0, SumNumbers<int>([]));
            QuizAssert.Equal(int.MinValue, SumNumbers<int>([int.MaxValue, 1]));
            QuizAssert.Throws<OverflowException>(() => SumNumbers<decimal>([decimal.MaxValue, 1m]));
        });
        suite.Add("Q12", () => QuizAssert.Equal(("string", "object", "string"), BindOverloads()));
        suite.Add("Q13", () => QuizAssert.Equal(("derived", "base", "derived"), DispatchMembers()));
        suite.Add("Q14", () => QuizAssert.Equal(("public", "interface", true), ExplicitCall()));
        suite.Add("Q15", () => QuizAssert.Equal(("positive", "text", "missing", "other"), MatchInputs()));
        suite.Add("Q16", () =>
        {
            QuizAssert.Equal(int.MinValue, CheckedCaller(int.MaxValue));
            QuizAssert.Throws<OverflowException>(() => CheckedAddition(int.MaxValue));
            QuizAssert.Throws<OverflowException>(() => UncheckedDecimal(decimal.MaxValue));
        });
        suite.Add("Q17", () => QuizAssert.Equal((false, true, false), MoneyArithmetic()));
        suite.Add("Q18", () => QuizAssert.Equal((4, 3, 2), CountText()));
        suite.Add("Q20", () => QuizAssert.Equal((false, -1, true), NullableThreshold()));
    }

    #region Q01
    private sealed class Session
    {
        public int Revision { get; set; }
    }

    private static void Update(Session session)
    {
        session.Revision = 2;
        session = new Session { Revision = 9 };
    }

    private static void Replace(ref Session session) =>
        session = new Session { Revision = 3 };

    private static (int AfterUpdate, int AfterReplace) PassReferences()
    {
        var session = new Session { Revision = 1 };
        Update(session);
        int first = session.Revision;
        Replace(ref session);
        return (first, session.Revision);
    }
    #endregion

    #region Q02
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
    #endregion

    #region Q04
    private readonly struct Settings
    {
        public string Name { get; }
        public Settings() => Name = "ready";
    }

    private static (string Constructed, bool DefaultIsNull, bool ArrayIsNull) DefaultSettings()
    {
        var constructed = new Settings();
        var zero = default(Settings);
        var slots = new Settings[1];
        return (constructed.Name, zero.Name is null, slots[0].Name is null);
    }
    #endregion

    #region Q05
    private static int NullSuppression()
    {
        string? externalName = null;
        string name = externalName!;
        return name.Length;
    }
    #endregion

    #region Q06
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
    #endregion

    #region Q07
    private sealed class Request
    {
        public required string? CorrelationId { get; init; }
        public required List<string> Tags { get; init; }
    }

    private static (bool MissingId, int TagCount) InitializeRequest()
    {
        var request = new Request { CorrelationId = null, Tags = ["draft"] };
        request.Tags.Add("approved");
        return (request.CorrelationId is null, request.Tags.Count);
    }
    #endregion

    #region Q08
    private sealed class CacheKey : IEquatable<CacheKey>
    {
        public required string Name { get; set; }
        public bool Equals(CacheKey? other) => other is not null && Name == other.Name;
        public override bool Equals(object? obj) => obj is CacheKey other && Equals(other);
        public override int GetHashCode() => StringComparer.Ordinal.GetHashCode(Name);
    }

    private static Dictionary<CacheKey, string> BuildCache()
    {
        var key = new CacheKey { Name = "before" };
        var cache = new Dictionary<CacheKey, string> { [key] = "payload" };
        key.Name = "after";
        return cache;
    }
    #endregion

    #region Q10
    // INumber<T> 位于 System.Numerics。
    private static T SumNumbers<T>(T[] numbers) where T : INumber<T>
    {
        T total = T.Zero;
        foreach (T number in numbers)
            total += number;
        return total;
    }
    #endregion

    #region Q12
    private static string Describe(string value) => "string";
    private static string Describe(object value) => "object";

    private static (string Inferred, string Object, string Dynamic) BindOverloads()
    {
        var inferred = "hello";
        object boxedView = inferred;
        dynamic dynamicView = inferred;
        return (Describe(inferred), Describe(boxedView), Describe(dynamicView));
    }
    #endregion

    #region Q13
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
    #endregion

    #region Q14
    private interface IFormatter
    {
        string Format();
    }

    private sealed class Formatter : IFormatter
    {
        public string Format() => "public";
        string IFormatter.Format() => "interface";
    }

    private static (string Concrete, string Interface, bool SameObject) ExplicitCall()
    {
        var formatter = new Formatter();
        IFormatter view = formatter;
        return (formatter.Format(), view.Format(), ReferenceEquals(formatter, view));
    }
    #endregion

    #region Q15
    private static string Classify(object? value) => value switch
    {
        int count when count > 0 => "positive",
        string { Length: > 0 } => "text",
        null => "missing",
        _ => "other"
    };

    private static (string Number, string Text, string Missing, string Negative) MatchInputs() =>
        (Classify(7), Classify("7"), Classify(null), Classify(-1));
    #endregion

    #region Q16
    private static int AddOne(int number) => number + 1;

    private static int CheckedCaller(int number)
    {
        checked
        {
            return AddOne(number);
        }
    }

    private static int CheckedAddition(int number) => checked(number + 1);

    private static decimal UncheckedDecimal(decimal number) => unchecked(number * 2m);
    #endregion

    #region Q17
    private static (bool BinarySum, bool DecimalSum, bool Thirds) MoneyArithmetic()
    {
        double binary = 0.1;
        decimal amount = 0.1m;
        decimal third = 1m / 3m;
        return (binary + 0.2 == 0.3, amount + 0.2m == 0.3m, third * 3m == 1m);
    }
    #endregion

    #region Q18
    private static (int CodeUnits, int Scalars, int TextElements) CountText()
    {
        string text = "\U0001F600e\u0301"; // 笑脸 + e + 组合重音
        int scalars = 0;
        foreach (var rune in text.EnumerateRunes())
            scalars++;
        return (text.Length, scalars,
            new System.Globalization.StringInfo(text).LengthInTextElements);
    }
    #endregion

    #region Q20
    private static (bool Exceeds, int Next, bool Missing) NullableThreshold()
    {
        int? threshold = null;
        bool exceeds = 100 > threshold;
        int next = (threshold + 1) ?? -1;
        return (exceeds, next, threshold == null);
    }
    #endregion
}
