internal static class QuizModeling
{
    internal static void Register(QuizSuite suite)
    {
        suite.Add("Q81", () => QuizAssert.Equal("base,derived", ConstructorOrder()));
        suite.Add("Q82", () => QuizAssert.Equal((5, 6), PrimaryState()));
        suite.Add("Q83", () => QuizAssert.Equal((3, true), GuardProperty()));
        suite.Add("Q84", () => QuizAssert.Equal((1, 2), ReadProperty()));
        suite.Add("Q85", () => QuizAssert.Equal((20, 99), IndexSlots()));
        suite.Add("Q86", () => QuizAssert.Equal(2, MutateReadOnlyReference()));
        suite.Add("Q88", () => QuizAssert.Equal((10, 20), OptionalDispatch()));
        suite.Add("Q89", () => QuizAssert.Equal((2, 1, "B,A"), NamedEvaluation()));
        suite.Add("Q90", () => QuizAssert.Equal(("default", true), DefaultInterface()));
        suite.Add("Q91", () => QuizAssert.Equal("begin,work,end", TemplateCall()));
        suite.Add("Q92", () => QuizAssert.Equal((1, 2, false), CopyPosition()));
        suite.Add("Q93", () => QuizAssert.Equal((true, false), AnonymousEquality()));
        suite.Add("Q94", () => QuizAssert.Equal((true, false), BindExtension()));
        suite.Add("Q95", () => QuizAssert.Equal(('c', true), ExtensionProperty()));
        suite.Add("Q96", () => QuizAssert.Equal(12, ConvertDistance()));
        suite.Add("Q97", () => QuizAssert.Equal((1, 3, false), AddVectors()));
        suite.Add("Q98", () => QuizAssert.Equal((10, "first,second"), InvokeDelegates()));
        suite.Add("Q99", () => QuizAssert.Equal((1, 1), EventAccessors()));
        suite.Add("Q100", () => QuizAssert.Equal(0, PartialHook.Run()));
    }

    #region Q81
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
    #endregion

    #region Q82
    private sealed class Sequence(int start)
    {
        public int Next() => start++;
    }
    private static (int First, int Second) PrimaryState()
    {
        var sequence = new Sequence(5);
        return (sequence.Next(), sequence.Next());
    }
    #endregion

    #region Q83
    private sealed class RetryPolicy
    {
        public int Limit
        {
            get;
            set => field = value >= 0 ? value : throw new ArgumentOutOfRangeException(nameof(value));
        }
    }
    private static (int Limit, bool Rejected) GuardProperty()
    {
        var policy = new RetryPolicy { Limit = 3 };
        bool rejected = false;
        try { policy.Limit = -1; }
        catch (ArgumentOutOfRangeException) { rejected = true; }
        return (policy.Limit, rejected);
    }
    #endregion

    #region Q84
    private sealed class Reading
    {
        private int reads;
        public int Value => ++reads;
    }
    private static (int First, int Second) ReadProperty()
    {
        var reading = new Reading();
        return (reading.Value, reading.Value);
    }
    #endregion

    #region Q85
    private sealed class Slots
    {
        private readonly int[] values = [10, 20];
        public int this[int index]
        {
            get => values[index];
            set => values[index] = value;
        }
    }
    private static (int Before, int After) IndexSlots()
    {
        var slots = new Slots();
        int before = slots[1];
        slots[1] = 99;
        return (before, slots[1]);
    }
    #endregion

    #region Q86
    private sealed class Tags
    {
        public readonly List<string> Items = ["draft"];
    }
    private static int MutateReadOnlyReference()
    {
        var tags = new Tags();
        tags.Items.Add("approved");
        return tags.Items.Count;
    }
    #endregion

    #region Q88
    private class BaseSender
    {
        public virtual int Send(int retries = 10) => retries;
    }
    private sealed class DerivedSender : BaseSender
    {
        public override int Send(int retries = 20) => retries;
    }
    private static (int ViaBase, int ViaDerived) OptionalDispatch()
    {
        var derived = new DerivedSender();
        BaseSender viaBase = derived;
        return (viaBase.Send(), derived.Send());
    }
    #endregion

    #region Q89
    private static (int First, int Second, string Trace) NamedEvaluation()
    {
        var trace = new List<string>();
        int Next(string label) { trace.Add(label); return trace.Count; }
        static (int, int) Pair(int first, int second) => (first, second);
        var pair = Pair(second: Next("B"), first: Next("A"));
        return (pair.Item1, pair.Item2, string.Join(',', trace));
    }
    #endregion

    #region Q90
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
    #endregion

    #region Q91
    private abstract class Job
    {
        public string Run()
        {
            var trace = new List<string> { "begin" };
            Execute(trace);
            trace.Add("end");
            return string.Join(',', trace);
        }
        protected abstract void Execute(List<string> trace);
    }
    private sealed class ImportJob : Job
    {
        protected override void Execute(List<string> trace) => trace.Add("work");
    }
    private static string TemplateCall() => new ImportJob().Run();
    #endregion

    #region Q92
    private readonly record struct Position(int X);
    private static (int Original, int Copy, bool Equal) CopyPosition()
    {
        var original = new Position(1);
        var copy = original with { X = 2 };
        return (original.X, copy.X, original == copy);
    }
    #endregion

    #region Q93
    private static (bool SameShape, bool DifferentOrder) AnonymousEquality()
    {
        var a = new { Name = "row", Count = 2 };
        var b = new { Name = "row", Count = 2 };
        var c = new { Count = 2, Name = "row" };
        return (a.Equals(b), a.Equals(c));
    }
    #endregion

    #region Q94-call
    private static (bool Instance, bool ExplicitStatic) BindExtension() =>
        ("abc".Contains("a"), QuizStringExtensions.Contains("abc", "a"));
    #endregion

    #region Q95-call
    private static (char First, bool NoRuntimeProperty) ExtensionProperty() =>
        ("cat".FirstUnit, typeof(string).GetProperty("FirstUnit") is null);
    #endregion

    #region Q96
    private readonly record struct Distance(int Metres)
    {
        public static implicit operator Distance(int value) => new(value);
        public static explicit operator int(Distance value) => value.Metres;
    }
    private static int ConvertDistance()
    {
        Distance distance = 12;
        return (int)distance;
    }
    #endregion

    #region Q97
    private sealed class Vector(int x)
    {
        public int X { get; } = x;
        public static Vector operator +(Vector a, Vector b) => new(a.X + b.X);
    }
    private static (int Left, int Sum, bool SameObject) AddVectors()
    {
        var left = new Vector(1);
        var sum = left + new Vector(2);
        return (left.X, sum.X, ReferenceEquals(left, sum));
    }
    #endregion

    #region Q98
    private static (int Result, string Trace) InvokeDelegates()
    {
        var trace = new List<string>();
        Func<int> handler = () => { trace.Add("first"); return 5; };
        handler += () => { trace.Add("second"); return 10; };
        return (handler(), string.Join(',', trace));
    }
    #endregion

    #region Q99
    private sealed class Subscription
    {
        public int Adds { get; private set; }
        public int Removes { get; private set; }
        public event Action Changed
        {
            add { Adds++; }
            remove { Removes++; }
        }
    }
    private static (int Adds, int Removes) EventAccessors()
    {
        var subscription = new Subscription();
        Action handler = () => { };
        subscription.Changed += handler;
        subscription.Changed -= handler;
        return (subscription.Adds, subscription.Removes);
    }
    #endregion

    #region Q100
    private partial class PartialHook
    {
        private static int calls;
        static partial void Observe(int value);
        private static int Next() => ++calls;
        public static int Run()
        {
            calls = 0;
            Observe(Next());
            return calls;
        }
    }
    #endregion
}

#region Q94-types
internal static class QuizStringExtensions
{
    public static bool Contains(this string text, string part) => false;
}
#endregion

#region Q95-types
internal static class QuizFirstUnitExtensions
{
    extension(string text)
    {
        public char FirstUnit => text[0];
    }
}
#endregion
