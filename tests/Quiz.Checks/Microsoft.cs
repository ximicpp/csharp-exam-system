using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static class QuizMicrosoft
{
    internal static void Register(QuizSuite suite)
    {
        suite.Add("Q124", () => QuizAssert.Equal("-2,-1", Q124()));
        suite.Add("Q125", () => QuizAssert.Equal("44,overflow", Q125()));
        suite.Add("Q126", () => QuizAssert.Equal("0.3", Q126()));
        suite.Add("Q127", () => QuizAssert.Equal("False,True,True", Q127()));
        suite.Add("Q128", () => QuizAssert.Equal("False,0", Q128()));
        suite.Add("Q129", () => QuizAssert.Equal("-1,0", Q129()));
        suite.Add("Q131", () => QuizAssert.Equal("draft.txt|final.txt", Q131()));
        suite.Add("Q132", () => QuizAssert.Equal("[  007]/2.5", Q132()));
        suite.Add("Q133", () => QuizAssert.Equal("3,2", Q133()));
        suite.Add("Q134", () => QuizAssert.Equal("False,True", Q134()));
        suite.Add("Q135", () => QuizAssert.Equal("0,True,2", Q135()));
        suite.Add("Q136", () => QuizAssert.Equal("1,2,4,8", Q136()));
        suite.Add("Q137", () => QuizAssert.Equal("True:7,4", Q137()));
        suite.Add("Q138", () => QuizAssert.Equal("True,0,False,0", Q138()));
        suite.Add("Q139", () => QuizAssert.Equal("rename,rename,1", Q139()));
        suite.Add("Q140", () => QuizAssert.Equal("True,False,2", Q140()));
        suite.Add("Q141", () => QuizAssert.Equal("guest,1", Q141()));
        suite.Add("Q142", () => QuizAssert.Equal("1,1", Q142()));
        suite.Add("Q143", () => QuizAssert.Equal("9,0", Q143()));
        suite.Add("Q144", () => QuizAssert.Equal("False,True,False", Q144()));
        suite.Add("Q145", () => QuizAssert.Equal("nonnegative", Q145()));
        suite.Add("Q146", () => QuizAssert.Equal("True,False", Q146()));
        suite.Add("Q147", () => QuizAssert.Equal("False,False,True", Q147()));
        suite.Add("Q148", () => QuizAssert.Equal("7", Q148()));
        suite.Add("Q149", () => QuizAssert.Equal("1,0", Q149()));
        suite.Add("Q151", () => QuizAssert.Equal("0,5,6", Q151()));
        suite.Add("Q152", () => QuizAssert.Equal("5", Q152()));
        suite.Add("Q153", () => QuizAssert.Equal("False,0", Q153()));
        suite.Add("Q154", () => QuizAssert.Equal("24", Q154()));
        suite.Add("Q155", () => QuizAssert.Equal("ready,9", Q155()));
        suite.Add("Q156", () => QuizAssert.Equal("int|double|decimal", Q156()));
        suite.Add("Q157", () => QuizAssert.Equal("2,4", Q157()));
        suite.Add("Q158", () => QuizAssert.Equal("1,2|1,2", Q158()));
        suite.Add("Q159", () => QuizAssert.Equal("item1,close", Q159()));
        suite.Add("Q161", () => QuizAssert.Equal("4", Q161()));
        suite.Add("Q162", () => QuizAssert.Equal("2", Q162()));
        suite.Add("Q163", () => QuizAssert.Equal("8", Q163()));
        suite.Add("Q164", () => QuizAssert.Equal("1,2,2", Q164()));
        suite.Add("Q165", () => QuizAssert.Equal("True,False", Q165()));
        suite.Add("Q166", () => QuizAssert.Equal("2,3|7,3", Q166()));
        suite.Add("Q168", () => QuizAssert.Equal("base+derived", Q168()));
        suite.Add("Q169", () => QuizAssert.Equal("2,2", Q169()));
        suite.Add("Q170", () => QuizAssert.Equal("6", Q170()));
        suite.Add("Q172", () => QuizAssert.Equal("3", Q172()));
        suite.Add("Q173", () => QuizAssert.Equal("Cat173", Q173()));
        suite.Add("Q174", () => QuizAssert.Equal("String", Q174()));
        suite.Add("Q175", () => QuizAssert.Equal("8,5,2", Q175()));
        suite.Add("Q176", () => QuizAssert.Equal("9", Q176()));
        suite.Add("Q177", () => QuizAssert.Equal("4,9", Q177()));
        suite.Add("Q178", () => QuizAssert.Equal("first,caught", Q178()));
        suite.Add("Q179", () => QuizAssert.Equal("1", Q179()));
        suite.Add("Q180", () => QuizAssert.Equal("Int32,String", Q180()));
        suite.Add("Q181", () => QuizAssert.Equal("try,catch,finally,after", Q181()));
        suite.Add("Q183", () => QuizAssert.Equal("cannot import|bad input", Q183()));
        suite.Add("Q184", () => QuizAssert.Equal("size", Q184()));
        suite.Add("Q185", () => QuizAssert.Equal("filter,fallback", Q185()));
        suite.Add("Q186", () => QuizAssert.Equal("body,tail,dispose,outer", Q186()));
        suite.Add("Q187", () => QuizAssert.Equal("A,True", Q187()));
        suite.AddAsync("Q188", async () => QuizAssert.Equal("dispose failed", await Q188()));
        suite.Add("Q189", () => QuizAssert.Equal("2,7,8,0", Q189()));
        suite.Add("Q190", () => QuizAssert.Equal("1", Q190()));
        suite.Add("Q191", () => QuizAssert.Equal("n8,n5", Q191()));
        suite.Add("Q192", () => QuizAssert.Equal("9|2", Q192()));
        suite.Add("Q193", () => QuizAssert.Equal("p:a,p:b,q:c", Q193()));
        suite.Add("Q194", () => QuizAssert.Equal("a:5,b:4", Q194()));
        suite.Add("Q195", () => QuizAssert.Equal("1:Lin,2:missing", Q195()));
        suite.Add("Q196", () => QuizAssert.Equal("c,b,a", Q196()));
        suite.Add("Q197", () => QuizAssert.Equal("30,40", Q197()));
        suite.Add("Q198", () => QuizAssert.Equal("True,False", Q198()));
        suite.Add("Q199", () => QuizAssert.Equal("2,3|0", Q199()));
        suite.Add("Q200", () => QuizAssert.Equal("2,3", Q200()));
        suite.AddAsync("Q201", async () => QuizAssert.Equal("True,6", await Q201()));
        suite.AddAsync("Q202", async () => QuizAssert.Equal("True,True", await Q202()));
        suite.AddAsync("Q203", async () => QuizAssert.Equal("10,20", await Q203()));
        suite.AddAsync("Q204", async () => QuizAssert.Equal("True,caught", await Q204()));
        suite.Add("Q205", () => QuizAssert.Equal("True,canceled", Q205()));
        suite.AddAsync("Q206", async () => QuizAssert.Equal("3", await Q206()));
        suite.AddAsync("Q207", async () => QuizAssert.Equal("item1,close", await Q207()));
        suite.AddAsync("Q208", async () => QuizAssert.Equal("True,0", await Q208()));
        suite.Add("Q209", () => QuizAssert.Equal("2,5,5", Q209()));
        suite.AddAsync("Q210", async () => QuizAssert.Equal("False,7", await Q210()));
        suite.Add("Q212", () => QuizAssert.Equal("True,True,False", Q212()));
        suite.Add("Q213", () => QuizAssert.Equal("4", Q213()));
        suite.Add("Q214", () => QuizAssert.Equal("GreaterThan,False", Q214()));
        suite.Add("Q215", () => QuizAssert.Equal("binding failed", Q215()));
        suite.Add("Q216", () => QuizAssert.Equal("1,9,3,4", Q216()));
        suite.Add("Q217", () => QuizAssert.Equal("[go]", Q217()));
        suite.Add("Q218", () => QuizAssert.Equal("True,False", Q218()));
        suite.Add("Q221", () => QuizAssert.Equal("3,8", Q221()));
        suite.Add("Q222", () => QuizAssert.Equal("8,True", Q222()));
        suite.Add("Q223", () => QuizAssert.Equal("5,0", Q223()));
        suite.Add("Q224", () => QuizAssert.Equal("True", Q224()));
        suite.Add("Q225", () => QuizAssert.Equal("7", Q225()));
        suite.Add("Q226", () => QuizAssert.Equal("3,True,False", Q226()));
        suite.Add("Q227", () => QuizAssert.Equal("4|2,3", Q227()));
        suite.Add("Q228", () => QuizAssert.Equal("0,9", Q228()));
        suite.Add("Q229", () => QuizAssert.Equal("7", Q229()));
        suite.Add("Q232", () => QuizAssert.Equal("4", Q232()));
        suite.Add("Q233", () => QuizAssert.Equal("7", Q233()));
        suite.Add("Q234", () => QuizAssert.Equal("4.0", Q234()));
        suite.Add("Q235", () => QuizAssert.Equal("2", Q235()));
        suite.Add("Q237", () => QuizAssert.Equal("release", Q237()));
    }

    #region Q124
    private static string Q124()
    {
        int offset = -7;
        return $"{offset / 3},{offset % 3}";
    }
    #endregion

    #region Q125
    private static string Q125()
    {
        int value = 300;
        byte wrapped = unchecked((byte)value);
        try { _ = checked((byte)value); }
        catch (OverflowException) { return $"{wrapped},overflow"; }
        return "no-error";
    }
    #endregion

    #region Q126
    private static string Q126()
    {
        decimal amount = 0.1m + 0.2m;
        return amount.ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q127
    private static string Q127()
    {
        double first = double.NaN;
        double second = double.NaN;
        return $"{first == second},{first.Equals(second)},{double.IsNaN(first)}";
    }
    #endregion

    #region Q128
    private static string Q128()
    {
        int? reading = null;
        int? adjusted = reading + 2;
        return $"{adjusted.HasValue},{adjusted.GetValueOrDefault()}";
    }
    #endregion

    #region Q129
    private static string Q129()
    {
        string? absent = null;
        string? blank = "   ";
        return $"{absent?.Trim().Length ?? -1},{blank?.Trim().Length ?? -1}";
    }
    #endregion

    #region Q131
    private static string Q131()
    {
        string name = "draft.txt";
        _ = name.Replace("draft", "final", StringComparison.Ordinal);
        string renamed = name.Replace("draft", "final", StringComparison.Ordinal);
        return $"{name}|{renamed}";
    }
    #endregion

    #region Q132
    private static string Q132()
    {
        int id = 7;
        double score = 2.5;
        return string.Create(CultureInfo.InvariantCulture, $"[{id,5:D3}]/{score:F1}");
    }
    #endregion

    #region Q133
    private static string Q133()
    {
        string text = "A\U0001F600";
        int scalars = 0;
        foreach (Rune rune in text.EnumerateRunes()) scalars++;
        return $"{text.Length},{scalars}";
    }
    #endregion

    #region Q134
    private static string Q134()
    {
        string path = @"C:\temp\new";
        return $"{path.Contains('\n')},{path.EndsWith(@"\new", StringComparison.Ordinal)}";
    }
    #endregion

    #region Q135
    private static string Q135()
    {
        int[] counts = new int[2];
        string?[] names = new string?[2];
        return $"{counts[0]},{names[0] is null},{counts.Length}";
    }
    #endregion

    #region Q136
    private static string Q136()
    {
        List<int> source = [2, 4];
        int[] packet = [1, .. source, 8];
        source.Add(6);
        return string.Join(",", packet);
    }
    #endregion

    #region Q137
    private static string Q137()
    {
        List<int> pending = [4, 7, 4];
        bool removed = pending.Remove(4);
        return $"{removed}:{string.Join(",", pending)}";
    }
    #endregion

    #region Q138
    private static string Q138()
    {
        Dictionary<string, int> config = new() { ["retry"] = 0 };
        bool found = config.TryGetValue("retry", out int retry);
        bool missing = config.TryGetValue("timeout", out int timeout);
        return $"{found},{retry},{missing},{timeout}";
    }
    #endregion

    #region Q139
    private static string Q139()
    {
        Stack<string> undo = new();
        undo.Push("edit");
        undo.Push("rename");
        string preview = undo.Peek();
        string removed = undo.Pop();
        return $"{preview},{removed},{undo.Count}";
    }
    #endregion

    #region Q140
    private static string Q140()
    {
        HashSet<int> seen = [5];
        bool first = seen.Add(8);
        bool duplicate = seen.Add(5);
        return $"{first},{duplicate},{seen.Count}";
    }
    #endregion

    #region Q141
    private static string Q141()
    {
        int calls = 0;
        string Fallback() { calls++; return "guest"; }
        string? name = null;
        name ??= Fallback();
        name ??= Fallback();
        return $"{name},{calls}";
    }
    #endregion

    #region Q142
    private static string Q142()
    {
        int calls = 0;
        int Next() => ++calls;
        bool fast = true;
        int chosen = fast ? Next() : Next() + 10;
        return $"{chosen},{calls}";
    }
    #endregion

    #region Q143
    private static string Q143()
    {
        int calls = 0;
        int Index() { calls++; return 0; }
        int[]? data = null;
        int value = data?[Index()] ?? 9;
        return $"{value},{calls}";
    }
    #endregion

    #region Q144
    private static string Q144()
    {
        bool a = true;
        bool b = true;
        return $"{a ^ b},{a ^ false},{!a}";
    }
    #endregion

    #region Q145
    private static string Q145()
    {
        static string Classify(int count) => count switch
        {
            int n when n >= 0 => "nonnegative",
            int n when n > 10 => "large",
            _ => "negative"
        };
        return Classify(20);
    }
    #endregion

    #region Q146
    private static string Q146()
    {
        static bool Valid(string[] args) => args is ["--limit", _];
        return $"{Valid(["--limit", "5"])},{Valid(["--limit", "5", "extra"])}";
    }
    #endregion

    #region Q147
    private sealed record Label147(string Text);

    private static string Q147()
    {
        Label147? missing = null;
        Label147 empty = new("");
        Label147 valid = new("go");
        return $"{missing is { Text.Length: > 0 }},{empty is { Text.Length: > 0 }},{valid is { Text.Length: > 0 }}";
    }
    #endregion

    #region Q148
    private static string Q148()
    {
        int total = 0;
        foreach (int value in new[] { 3, -2, 4, 0, 9 })
        {
            if (value < 0) continue;
            if (value == 0) break;
            total += value;
        }
        return total.ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q149
    private static string Q149()
    {
        int first = 0;
        int second = 0;
        do { first++; } while (first < 0);
        while (second < 0) { second++; }
        return $"{first},{second}";
    }
    #endregion

    #region Q151
    private static string Q151()
    {
        static int Total(params int[] values) => values.Sum();
        int[] pair = [2, 3];
        return $"{Total()},{Total(pair)},{Total(1, 2, 3)}";
    }
    #endregion

    #region Q152
    private static string Q152()
    {
        static void Advance(ref int position) => position += 2;
        int cursor = 3;
        Advance(ref cursor);
        return cursor.ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q153
    private static string Q153()
    {
        int value = 17;
        bool ok = int.TryParse("not-a-number", NumberStyles.Integer, CultureInfo.InvariantCulture, out value);
        return $"{ok},{value}";
    }
    #endregion

    #region Q154
    private static string Q154()
    {
        int result = Factorial(4);
        return result.ToString(CultureInfo.InvariantCulture);

        static int Factorial(int n) => n <= 1 ? 1 : n * Factorial(n - 1);
    }
    #endregion

    #region Q155
    private static string Q155()
    {
        int count = 9;
        (string status, _) = ("ready", 3);
        return $"{status},{count}";
    }
    #endregion

    #region Q156
    private static string Tag156(int value) => "int";
    private static string Tag156(double value) => "double";
    private static string Tag156(decimal value) => "decimal";

    private static string Q156()
    {
        return $"{Tag156(1)}|{Tag156(1.0)}|{Tag156(1.0m)}";
    }
    #endregion

    #region Q157
    private static IEnumerable<int> Read157()
    {
        foreach (int value in new[] { 2, 4, 0, 8 })
        {
            if (value == 0) yield break;
            yield return value;
        }
    }

    private static string Q157()
    {
        return string.Join(",", Read157());
    }
    #endregion

    #region Q158
    private static IEnumerable<int> Count158()
    {
        yield return 1;
        yield return 2;
    }

    private static string Q158()
    {
        IEnumerable<int> values = Count158();
        return $"{string.Join(",", values)}|{string.Join(",", values)}";
    }
    #endregion

    #region Q159
    private static IEnumerable<int> Read159(List<string> log)
    {
        try { yield return 1; yield return 2; }
        finally { log.Add("close"); }
    }

    private static string Q159()
    {
        List<string> log = [];
        foreach (int value in Read159(log)) { log.Add($"item{value}"); break; }
        return string.Join(",", log);
    }
    #endregion

    #region Q161
    private class Store161
    {
        public int Capacity { get; }
        public Store161(int capacity) => Capacity = capacity;
    }
    private sealed class Worker161 : Store161
    {
        public Worker161(int seed) : base(seed + 1) { }
    }

    private static string Q161()
    {
        Worker161 worker = new(3);
        return worker.Capacity.ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q162
    private sealed class Counter162
    {
        public int Count { get; private set; }
        public void Increment() => Count++;
    }

    private static string Q162()
    {
        Counter162 counter = new();
        counter.Increment();
        counter.Increment();
        return counter.Count.ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q163
    private sealed class Settings163
    {
        public int Level { get; set; }
        public Settings163() => Level = 3;
    }

    private static string Q163()
    {
        Settings163 options = new() { Level = 8 };
        return options.Level.ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q164
    private sealed class Ticket164
    {
        public static int Created;
        public int Id { get; } = ++Created;
    }

    private static string Q164()
    {
        Ticket164.Created = 0;
        Ticket164 first = new();
        Ticket164 second = new();
        return $"{first.Id},{second.Id},{Ticket164.Created}";
    }
    #endregion

    #region Q165
    private sealed record Person165(string Name);
    private sealed class Plain165(string name)
    {
        public string Name { get; } = name;
    }

    private static string Q165()
    {
        Person165 a = new("Lin");
        Person165 b = new("Lin");
        Plain165 x = new("Lin");
        Plain165 y = new("Lin");
        return $"{a == b},{x == y}";
    }
    #endregion

    #region Q166
    private record struct Point166(int X, int Y);

    private static string Q166()
    {
        Point166 start = new(2, 3);
        Point166 moved = start with { X = 7 };
        return $"{start.X},{start.Y}|{moved.X},{moved.Y}";
    }
    #endregion

    #region Q168
    private class Base168
    {
        public virtual string Name() => "base";
    }
    private sealed class Derived168 : Base168
    {
        public override string Name() => base.Name() + "+derived";
    }

    private static string Q168()
    {
        Base168 value = new Derived168();
        return value.Name();
    }
    #endregion

    #region Q169
    private static string Q169()
    {
        int[] values = [-1, 2, 3];
        int instanceStyle = values.Count(v => v > 0);
        int staticStyle = Enumerable.Count(values, v => v > 0);
        return $"{instanceStyle},{staticStyle}";
    }
    #endregion

    #region Q170
    private interface IIdentified170 { int Id { get; } }
    private sealed class Entity170 : IIdentified170
    {
        public int Id { get; init; }
        public string Name { get; init; } = "";
    }

    private static string Q170()
    {
        IIdentified170 item = new Entity170 { Id = 6, Name = "job" };
        return item.Id.ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q172
    private static T Smaller172<T>(T left, T right) where T : IComparable<T>
        => left.CompareTo(right) <= 0 ? left : right;

    private static string Q172()
    {
        return Smaller172(8, 3).ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q173
    private class Animal173 { }
    private sealed class Cat173 : Animal173 { }

    private static string Q173()
    {
        IEnumerable<Cat173> cats = new List<Cat173> { new() };
        IEnumerable<Animal173> animals = cats;
        return animals.Single().GetType().Name;
    }
    #endregion

    #region Q174
    private static string Q174()
    {
        string log = "";
        Action<object> record = value => log = value.GetType().Name;
        Action<string> acceptText = record;
        acceptText("hello");
        return log;
    }
    #endregion

    #region Q175
    private static string Q175()
    {
        int[] values = [2, 8, 5];
        Array.Sort(values, Comparer<int>.Create((left, right) => right.CompareTo(left)));
        return string.Join(",", values);
    }
    #endregion

    #region Q176
    private static string Q176()
    {
        Func<int, int> twice = value => value * 2;
        Func<int, int> next = value => twice(value) + 1;
        return next(4).ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q177
    private static string Q177()
    {
        int[] values = [2, 3];
        return string.Join(",", values.Select(static value => value * value));
    }
    #endregion

    #region Q178
    private static string Q178()
    {
        List<string> log = [];
        Action handlers = () => log.Add("first");
        handlers += () => throw new InvalidOperationException("broken");
        handlers += () => log.Add("last");
        try { handlers(); }
        catch (InvalidOperationException) { log.Add("caught"); }
        return string.Join(",", log);
    }
    #endregion

    #region Q179
    private sealed class Publisher179
    {
        public event Action? Changed;
        public void Raise() => Changed?.Invoke();
    }

    private static string Q179()
    {
        Publisher179 source = new();
        int calls = 0;
        Action handler = () => calls++;
        source.Changed += handler;
        source.Raise();
        source.Changed -= handler;
        source.Raise();
        return calls.ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q180
    private static T Identity180<T>(T value) => value;

    private static string Q180()
    {
        var number = Identity180(3);
        var text = Identity180("three");
        return $"{number.GetType().Name},{text.GetType().Name}";
    }
    #endregion

    #region Q181
    private static string Q181()
    {
        List<string> log = [];
        try { log.Add("try"); throw new FormatException(); }
        catch (FormatException) { log.Add("catch"); }
        finally { log.Add("finally"); }
        log.Add("after");
        return string.Join(",", log);
    }
    #endregion

    #region Q183
    private static string Q183()
    {
        Exception original = new FormatException("bad input");
        Exception wrapped = new InvalidOperationException("cannot import", original);
        return $"{wrapped.Message}|{wrapped.InnerException?.Message}";
    }
    #endregion

    #region Q184
    private static string Q184()
    {
        static void Validate(int size)
        {
            if (size <= 0) throw new ArgumentOutOfRangeException(nameof(size));
        }
        try { Validate(0); }
        catch (ArgumentOutOfRangeException error) { return error.ParamName ?? "missing"; }
        return "accepted";
    }
    #endregion

    #region Q185
    private static string Q185()
    {
        List<string> log = [];
        bool Accept() { log.Add("filter"); return false; }
        try { throw new InvalidOperationException(); }
        catch (InvalidOperationException) when (Accept()) { log.Add("first"); }
        catch (InvalidOperationException) { log.Add("fallback"); }
        return string.Join(",", log);
    }
    #endregion

    #region Q186
    private sealed class Resource186(List<string> log) : IDisposable
    {
        public void Dispose() => log.Add("dispose");
    }

    private static string Q186()
    {
        List<string> log = [];
        {
            using var resource = new Resource186(log);
            log.Add("body");
            log.Add("tail");
        }
        log.Add("outer");
        return string.Join(",", log);
    }
    #endregion

    #region Q187
    private static string Q187()
    {
        using MemoryStream stream = new([65]);
        string text;
        using (StreamReader reader = new(stream, Encoding.UTF8, false, 128, leaveOpen: true))
            text = reader.ReadToEnd();
        return $"{text},{stream.CanRead}";
    }
    #endregion

    #region Q188
    private sealed class Resource188 : IAsyncDisposable
    {
        public ValueTask DisposeAsync() => ValueTask.FromException(new InvalidOperationException("dispose failed"));
    }

    private static async Task<string> Q188()
    {
        try
        {
            await using var resource = new Resource188();
        }
        catch (InvalidOperationException error) { return error.Message; }
        return "success";
    }
    #endregion

    #region Q189
    private static string Q189()
    {
        using MemoryStream stream = new([7, 8]);
        byte[] buffer = new byte[5];
        int count = stream.Read(buffer, 0, buffer.Length);
        return $"{count},{buffer[0]},{buffer[1]},{buffer[2]}";
    }
    #endregion

    #region Q190
    private static string Q190()
    {
        IDisposable? optional = null;
        int calls = 0;
        using (optional) { calls++; }
        return calls.ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q191
    private static string Q191()
    {
        int[] scores = [3, 8, 5];
        var query = from score in scores where score > 3 orderby score descending select $"n{score}";
        return string.Join(",", query);
    }
    #endregion

    #region Q192
    private static string Q192()
    {
        int calls = 0;
        int Square(int value) { calls++; return value * value; }
        int[] source = [2, 3];
        var query = from value in source let square = Square(value) where square > 4 select square;
        string result = string.Join(",", query);
        return $"{result}|{calls}";
    }
    #endregion

    #region Q193
    private static string Q193()
    {
        var projects = new[] { (Name: "p", Items: new[] { "a", "b" }), (Name: "q", Items: new[] { "c" }) };
        var rows = projects.SelectMany(project => project.Items, (project, item) => $"{project.Name}:{item}");
        return string.Join(",", rows);
    }
    #endregion

    #region Q194
    private static string Q194()
    {
        var entries = new[] { (Team: "a", Count: 2), (Team: "b", Count: 4), (Team: "a", Count: 3) };
        var totals = entries.GroupBy(row => row.Team).OrderBy(group => group.Key, StringComparer.Ordinal)
            .Select(group => $"{group.Key}:{group.Sum(row => row.Count)}");
        return string.Join(",", totals);
    }
    #endregion

    #region Q195
    private static string Q195()
    {
        int[] orders = [1, 2];
        var customers = new[] { (Id: 1, Name: "Lin") };
        var rows = from id in orders
                   join customer in customers on id equals customer.Id into matches
                   from customer in matches.DefaultIfEmpty()
                   select $"{id}:{customer.Name ?? "missing"}";
        return string.Join(",", rows);
    }
    #endregion

    #region Q196
    private static string Q196()
    {
        var tasks = new[] { (Name: "b", Priority: 1), (Name: "a", Priority: 1), (Name: "c", Priority: 0) };
        return string.Join(",", tasks.OrderBy(task => task.Priority).Select(task => task.Name));
    }
    #endregion

    #region Q197
    private static string Q197()
    {
        int[] items = [10, 20, 30, 40, 50];
        return string.Join(",", items.Skip(2).Take(2));
    }
    #endregion

    #region Q198
    private static string Q198()
    {
        int[] values = [];
        return $"{values.All(value => value > 0)},{values.Any()}";
    }
    #endregion

    #region Q199
    private static string Q199()
    {
        var entries = new[] { (User: "u", Value: 2), (User: "u", Value: 3) };
        var lookup = entries.ToLookup(row => row.User, row => row.Value);
        return $"{string.Join(",", lookup["u"])}|{lookup["absent"].Count()}";
    }
    #endregion

    #region Q200
    private static string Q200()
    {
        List<int> source = [1, 2];
        var query = source.Where(value => value > 1);
        source.Add(3);
        int[] snapshot = query.ToArray();
        source.Add(4);
        return string.Join(",", snapshot);
    }
    #endregion

    #region Q201
    private static async Task<int> Answer201() => await Task.FromResult(5) + 1;

    private static async Task<string> Q201()
    {
        Task<int> result = Answer201();
        return $"{result.IsCompletedSuccessfully},{await result}";
    }
    #endregion

    #region Q202
    private static async Task<string> Q202()
    {
        Task<int> failed = Task.FromException<int>(new InvalidOperationException("failed"));
        var pending = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
        Task<int> winner = await Task.WhenAny(failed, pending.Task);
        try { _ = await winner; }
        catch (InvalidOperationException) { pending.SetResult(0); return $"{ReferenceEquals(winner, failed)},{winner.IsFaulted}"; }
        return "success";
    }
    #endregion

    #region Q203
    private static async Task<string> Q203()
    {
        var first = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
        var second = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
        Task<int[]> combined = Task.WhenAll(first.Task, second.Task);
        second.SetResult(20);
        first.SetResult(10);
        return string.Join(",", await combined);
    }
    #endregion

    #region Q204
    private static async Task<int> Fail204()
    {
        int value = int.Parse("bad", CultureInfo.InvariantCulture);
        await Task.CompletedTask;
        return value;
    }

    private static async Task<string> Q204()
    {
        Task<int> task = Fail204();
        try { _ = await task; }
        catch (FormatException) { return $"{task.IsFaulted},caught"; }
        return "success";
    }
    #endregion

    #region Q205
    private static string Q205()
    {
        CancellationToken token = new(canceled: true);
        try { token.ThrowIfCancellationRequested(); }
        catch (OperationCanceledException error) { return $"{error.CancellationToken == token},canceled"; }
        return "continued";
    }
    #endregion

    #region Q206
    private static async IAsyncEnumerable<int> Read206()
    {
        yield return 1;
        await Task.CompletedTask;
        yield return 2;
    }

    private static async Task<string> Q206()
    {
        int total = 0;
        await foreach (int value in Read206()) total += value;
        return total.ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q207
    private static async IAsyncEnumerable<int> Read207(List<string> log)
    {
        try
        {
            yield return 1;
            await Task.CompletedTask;
            yield return 2;
        }
        finally { log.Add("close"); }
    }

    private static async Task<string> Q207()
    {
        List<string> log = [];
        await foreach (int value in Read207(log)) { log.Add($"item{value}"); break; }
        return string.Join(",", log);
    }
    #endregion

    #region Q208
    private static async Task<string> Q208()
    {
        using SemaphoreSlim gate = new(1, 1);
        await gate.WaitAsync();
        Task next = gate.WaitAsync();
        bool waiting = !next.IsCompleted;
        gate.Release();
        await next;
        int available = gate.CurrentCount;
        gate.Release();
        return $"{waiting},{available}";
    }
    #endregion

    #region Q209
    private static string Q209()
    {
        int state = 2;
        int before = Interlocked.CompareExchange(ref state, 5, 2);
        int rejected = Interlocked.CompareExchange(ref state, 9, 2);
        return $"{before},{rejected},{state}";
    }
    #endregion

    #region Q210
    private static async Task<string> Q210()
    {
        var work = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
        CancellationToken token = new(canceled: true);
        try { _ = await work.Task.WaitAsync(token); }
        catch (OperationCanceledException)
        {
            bool originalCompleted = work.Task.IsCompleted;
            work.SetResult(7);
            return $"{originalCompleted},{await work.Task}";
        }
        return "unexpected";
    }
    #endregion

    #region Q212
    private static string Q212()
    {
        Type closed = typeof(List<int>);
        Type definition = closed.GetGenericTypeDefinition();
        return $"{closed.IsGenericType},{definition == typeof(List<>)},{closed == definition}";
    }
    #endregion

    #region Q213
    [AttributeUsage(AttributeTargets.Class)]
    private sealed class Priority213Attribute(int value) : Attribute
    {
        public int Value { get; } = value;
    }
    [Priority213(4)]
    private sealed class Job213 { }

    private static string Q213()
    {
        var attribute = typeof(Job213).GetCustomAttribute<Priority213Attribute>();
        return attribute?.Value.ToString(CultureInfo.InvariantCulture) ?? "missing";
    }
    #endregion

    #region Q214
    private static string Q214()
    {
        int limit = 3;
        Expression<Func<int, bool>> rule = value => value > limit;
        Func<int, bool> compiled = rule.Compile();
        limit = 8;
        return $"{rule.Body.NodeType},{compiled(5)}";
    }
    #endregion

    #region Q215
    private static string Q215()
    {
        dynamic text = "hello";
        try { _ = text.MissingMember(); }
        catch (Microsoft.CSharp.RuntimeBinder.RuntimeBinderException) { return "binding failed"; }
        return "success";
    }
    #endregion

    #region Q216
    private static string Q216()
    {
        int[] data = [1, 2, 3, 4];
        Span<int> middle = data.AsSpan(1, 2);
        middle[0] = 9;
        return string.Join(",", data);
    }
    #endregion

    #region Q217
    private sealed class Label217
    {
        public string Text { get; set => field = value.Trim(); } = "";
    }

    private static string Q217()
    {
        Label217 label = new() { Text = "  go  " };
        return $"[{label.Text}]";
    }
    #endregion

    #region Q218
    private static string Q218()
    {
        string text = "go";
        return $"{text.HasContent},{"".HasContent}";
    }
    #endregion

    #region Q221
    private struct Position221 { public int X; }

    private static string Q221()
    {
        Position221 start = new() { X = 3 };
        Position221 copy = start;
        copy.X = 8;
        return $"{start.X},{copy.X}";
    }
    #endregion

    #region Q222
    private sealed class Box222 { public int Value; }

    private static string Q222()
    {
        Box222 first = new() { Value = 3 };
        Box222 second = first;
        second.Value = 8;
        return $"{first.Value},{ReferenceEquals(first, second)}";
    }
    #endregion

    #region Q223
    private struct Options223
    {
        public int Limit;
        public Options223() => Limit = 5;
    }

    private static string Q223()
    {
        Options223 constructed = new();
        Options223 zeroed = default;
        return $"{constructed.Limit},{zeroed.Limit}";
    }
    #endregion

    #region Q224
    private static string Q224()
    {
        string? raw = null;
        string assumed = raw!;
        return (assumed is null).ToString();
    }
    #endregion

    #region Q225
    private sealed class Token225
    {
        public readonly int Id;
        public Token225(int id) => Id = id;
    }

    private static string Q225()
    {
        Token225 value = new(7);
        return value.Id.ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q226
    [Flags]
    private enum Access226 { None = 0, Read = 1, Write = 2, Execute = 4 }

    private static string Q226()
    {
        Access226 permissions = Access226.Read | Access226.Write;
        return $"{(int)permissions},{permissions.HasFlag(Access226.Write)},{permissions.HasFlag(Access226.Execute)}";
    }
    #endregion

    #region Q227
    private static string Q227()
    {
        int[] values = [1, 2, 3, 4];
        int last = values[^1];
        int[] middle = values[1..^1];
        return $"{last}|{string.Join(",", middle)}";
    }
    #endregion

    #region Q228
    private sealed class Slots228
    {
        private readonly int[] data = new int[2];
        public int this[int index] { get => data[index]; set => data[index] = value; }
    }

    private static string Q228()
    {
        Slots228 slots = new();
        slots[1] = 9;
        return $"{slots[0]},{slots[1]}";
    }
    #endregion

    #region Q229
    private readonly record struct Distance229(int Meters)
    {
        public static Distance229 operator +(Distance229 left, Distance229 right) => new(left.Meters + right.Meters);
    }

    private static string Q229()
    {
        Distance229 first = new(3);
        Distance229 second = new(4);
        return (first + second).Meters.ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q232
    private sealed class Cursor232(int position)
    {
        public void Move() => position++;
        public int Position() => position;
    }

    private static string Q232()
    {
        Cursor232 cursor = new(3);
        cursor.Move();
        return cursor.Position().ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q233
    private abstract class Pipeline233
    {
        protected abstract int Step(int value);
        public int Run(int value) => Step(value) + 1;
    }
    private sealed class Double233 : Pipeline233
    {
        protected override int Step(int value) => value * 2;
    }

    private static string Q233()
    {
        Pipeline233 pipeline = new Double233();
        return pipeline.Run(3).ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q234
    private static T Add234<T>(T left, T right) where T : System.Numerics.INumber<T>
        => left + right;

    private static string Q234()
    {
        return Add234(1.5m, 2.5m).ToString("F1", CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q235
    private static string Q235()
    {
        object gate = new();
        int count = 0;
        lock (gate) { count++; lock (gate) { count++; } }
        return count.ToString(CultureInfo.InvariantCulture);
    }
    #endregion

    #region Q237
    private static string Q237()
    {
        #if DEBUG
        return "debug";
        #else
        return "release";
        #endif
    }
    #endregion
}

#region Q218-extension
internal static class MicrosoftTextExtensions
{
    extension(string text)
    {
        public bool HasContent => text.Length > 0;
    }
}
#endregion
