using System.Linq.Expressions;
using System.Reflection;

internal static class QuizQueries
{
    internal static void Register(QuizSuite suite)
    {
        suite.Add("Q101", () => QuizAssert.Equal("20,30", FilterProject()));
        suite.Add("Q102", () => QuizAssert.Equal("1,2,3", Flatten()));
        suite.Add("Q103", () => QuizAssert.Equal(("a1,a2,b1", "a1,b1,a2"), SortKeys()));
        suite.Add("Q104", () => QuizAssert.Equal((1, "red", 2), GroupKeys()));
        suite.Add("Q105", () => QuizAssert.Equal("1:10,1:20", JoinRows()));
        suite.Add("Q106", () => QuizAssert.Equal("a:2,b:0", GroupJoinRows()));
        suite.Add("Q107", () => QuizAssert.Equal(2, DistinctKeys()));
        suite.Add("Q108", () => QuizAssert.Throws<ArgumentException>(() => DuplicateDictionary()));
        suite.Add("Q109", () => QuizAssert.Equal((4, true), SelectOne()));
        suite.Add("Q110", () => QuizAssert.Equal((true, 1), Existential()));
        suite.Add("Q111", () => QuizAssert.Equal((10, true), EmptyAggregate()));
        suite.Add("Q112", () => QuizAssert.Equal("1:a,2:b", ZipRows()));
        suite.Add("Q113", () => QuizAssert.Equal(("Add", 3), InspectExpression()));
        suite.Add("Q114", () => QuizAssert.Equal((3, -1), RebuildExpression()));
        suite.Add("Q115", () => QuizAssert.Equal(("Name", 0), NameWithoutRead()));
        suite.Add("Q116", () => QuizAssert.Equal(("Object", "String", true), RuntimeType()));
        suite.Add("Q117", () => QuizAssert.Equal((0, 1, -1), ReadAttribute()));
        suite.Add("Q118", () => QuizAssert.True(ReflectionFailure(), "Missing wrapped target exception"));
    }

    #region Q101
    private static string FilterProject()
    {
        int[] values = [1, 2, 3];
        var result = values.Where(x => x >= 2).Select(x => x * 10);
        return string.Join(',', result);
    }
    #endregion

    #region Q102
    private static string Flatten()
    {
        int[][] batches = [[1, 2], [], [3]];
        return string.Join(',', batches.SelectMany(batch => batch));
    }
    #endregion

    #region Q103
    private static (string AdditionalKey, string NewPrimaryKey) SortKeys()
    {
        (string Name, int Rank)[] rows = [("b", 1), ("a", 2), ("a", 1)];
        var additional = rows.OrderBy(x => x.Name, StringComparer.Ordinal).ThenBy(x => x.Rank);
        var replaced = rows.OrderBy(x => x.Name, StringComparer.Ordinal).OrderBy(x => x.Rank);
        static string Show(IEnumerable<(string Name, int Rank)> items) =>
            string.Join(',', items.Select(x => $"{x.Name}{x.Rank}"));
        return (Show(additional), Show(replaced));
    }
    #endregion

    #region Q104
    private static (int Groups, string Key, int Items) GroupKeys()
    {
        string[] names = ["red", "RED"];
        var groups = names.GroupBy(x => x, StringComparer.OrdinalIgnoreCase).ToArray();
        return (groups.Length, groups[0].Key, groups[0].Count());
    }
    #endregion

    #region Q105
    private static string JoinRows()
    {
        int[] left = [1, 2];
        (int Key, int Value)[] right = [(1, 10), (1, 20), (3, 30)];
        var rows = left.Join(right, x => x, x => x.Key, (l, r) => $"{l}:{r.Value}");
        return string.Join(',', rows);
    }
    #endregion

    #region Q106
    private static string GroupJoinRows()
    {
        (int Key, string Name)[] left = [(1, "a"), (2, "b")];
        int[] right = [1, 1, 3];
        var rows = left.GroupJoin(right, x => x.Key, x => x,
            (l, matches) => $"{l.Name}:{matches.Count()}");
        return string.Join(',', rows);
    }
    #endregion

    #region Q107
    private static int DistinctKeys()
    {
        string[] keys = ["a", "A", "b"];
        return keys.Distinct(StringComparer.OrdinalIgnoreCase).Count();
    }
    #endregion

    #region Q108
    private static Dictionary<string, int> DuplicateDictionary()
    {
        (string Key, int Value)[] rows = [("same", 1), ("same", 2)];
        return rows.ToDictionary(x => x.Key, x => x.Value, StringComparer.Ordinal);
    }
    #endregion

    #region Q109
    private static (int First, bool SingleRejected) SelectOne()
    {
        int[] values = [4, 4];
        int first = values.First();
        bool rejected = false;
        try { _ = values.Single(); }
        catch (InvalidOperationException) { rejected = true; }
        return (first, rejected);
    }
    #endregion

    #region Q110
    private static (bool Found, int PredicateCalls) Existential()
    {
        int calls = 0;
        int[] values = [2, 4, 6];
        bool found = values.Where(x => { calls++; return x > 0; }).Any();
        return (found, calls);
    }
    #endregion

    #region Q111
    private static (int Seeded, bool UnseededRejected) EmptyAggregate()
    {
        int[] values = [];
        int seeded = values.Aggregate(10, (acc, x) => acc + x);
        bool rejected = false;
        try { _ = values.Aggregate((acc, x) => acc + x); }
        catch (InvalidOperationException) { rejected = true; }
        return (seeded, rejected);
    }
    #endregion

    #region Q112
    private static string ZipRows()
    {
        int[] ids = [1, 2, 3];
        string[] labels = ["a", "b"];
        return string.Join(',', ids.Zip(labels, (id, label) => $"{id}:{label}"));
    }
    #endregion

    #region Q113
    private static (string Node, int Result) InspectExpression()
    {
        Expression<Func<int, int>> expression = x => x + 1;
        return (expression.Body.NodeType.ToString(), expression.Compile()(2));
    }
    #endregion

    #region Q114
    private static (int Original, int Replacement) RebuildExpression()
    {
        var original = Expression.Add(Expression.Constant(1), Expression.Constant(2));
        var replacement = Expression.Subtract(original.Left, original.Right);
        int first = Expression.Lambda<Func<int>>(original).Compile()();
        int second = Expression.Lambda<Func<int>>(replacement).Compile()();
        return (first, second);
    }
    #endregion

    #region Q115
    private sealed class Tracked
    {
        public int Reads { get; private set; }
        public string Name { get { Reads++; return "row"; } }
    }
    private static (string Name, int Reads) NameWithoutRead()
    {
        var tracked = new Tracked();
        string name = nameof(tracked.Name);
        return (name, tracked.Reads);
    }
    #endregion

    #region Q116
    private static (string StaticType, string ActualType, bool Assignable) RuntimeType()
    {
        object value = "row";
        return (typeof(object).Name, value.GetType().Name,
            typeof(object).IsAssignableFrom(value.GetType()));
    }
    #endregion

    #region Q117
    [AttributeUsage(AttributeTargets.Property)]
    private sealed class PositiveAttribute : Attribute
    {
        public static int Constructions { get; set; }
        public PositiveAttribute() => Constructions++;
    }
    private sealed class Measurement
    {
        [Positive]
        public int Value { get; set; }
    }
    private static (int BeforeRead, int AfterRead, int Value) ReadAttribute()
    {
        PositiveAttribute.Constructions = 0;
        var measurement = new Measurement { Value = -1 };
        int before = PositiveAttribute.Constructions;
        var property = typeof(Measurement).GetProperty(nameof(Measurement.Value))!;
        _ = property.GetCustomAttribute<PositiveAttribute>();
        return (before, PositiveAttribute.Constructions, measurement.Value);
    }
    #endregion

    #region Q118
    private sealed class Failing
    {
        public void Run() => throw new InvalidOperationException("broken");
    }
    private static bool ReflectionFailure()
    {
        var method = typeof(Failing).GetMethod(nameof(Failing.Run))!;
        try { method.Invoke(new Failing(), null); }
        catch (TargetInvocationException error)
        {
            return error.InnerException is InvalidOperationException;
        }
        return false;
    }
    #endregion
}
