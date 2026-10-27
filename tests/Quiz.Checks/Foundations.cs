internal static class QuizFoundations
{
    internal static void Register(QuizSuite suite)
    {
        suite.Add("Q63", () => QuizAssert.Equal((0d, 0.75d), CompletionRatios()));
        suite.Add("Q64", () => QuizAssert.Equal((260, true), AddBytes()));
        suite.Add("Q65", () => QuizAssert.Equal((1, 11, 2), UpdateBucket()));
        suite.Add("Q66", () => QuizAssert.Equal((false, false, 1), EvaluateConditions()));
        suite.Add("Q67", () => QuizAssert.Equal((0, 9, 1), ResolveLengths()));
        suite.Add("Q68", () => QuizAssert.Equal((false, true), CheckPermissions()));
        suite.Add("Q69", () => QuizAssert.Equal((true, false, 8), ParseMode()));
        suite.Add("Q70", () => QuizAssert.Equal((10, 3, 3, 10), RenameTuple()));
        suite.Add("Q71", () => QuizAssert.Throws<ArrayTypeMismatchException>(WriteThroughObjectArray));
        suite.Add("Q72", () => QuizAssert.Equal((6, 2, 2, 1), ArrayShapes()));
        suite.Add("Q73", () => QuizAssert.Equal((20, 2, 99), SliceArray()));
        suite.Add("Q75", () => QuizAssert.Equal("header|  \"value\"", ReadRawText()));
        suite.Add("Q76", () => QuizAssert.Equal("{\"count\": 3}", FormatRawJson()));
        suite.Add("Q78", () => QuizAssert.Equal(("3,3,3", "0,1,2"), CaptureLoops()));
        suite.Add("Q80", () => QuizAssert.Equal(("12,5", "12.5"), FormatAmount()));
    }

    #region Q63
    private static (double AfterDivision, double BeforeDivision) CompletionRatios()
    {
        int completed = 3;
        int total = 4;
        double first = completed / total;
        double second = (double)completed / total;
        return (first, second);
    }
    #endregion

    #region Q64
    private static (int Value, bool IsInt) AddBytes()
    {
        byte left = 200;
        byte right = 60;
        var total = left + right;
        return (total, total.GetType() == typeof(int));
    }
    #endregion

    #region Q65
    private static (int Index, int First, int Second) UpdateBucket()
    {
        int[] buckets = [1, 2];
        int index = 0;
        buckets[index++] += 10;
        return (index, buckets[0], buckets[1]);
    }
    #endregion

    #region Q66
    private static (bool ShortCircuit, bool Eager, int Calls) EvaluateConditions()
    {
        int calls = 0;
        bool Probe()
        {
            calls++;
            return true;
        }

        bool ready = false;
        bool first = ready && Probe();
        bool second = ready & Probe();
        return (first, second, calls);
    }
    #endregion

    #region Q67
    private static (int Empty, int Missing, int FallbackCalls) ResolveLengths()
    {
        int calls = 0;
        int Fallback()
        {
            calls++;
            return 9;
        }

        string? empty = "";
        string? missing = null;
        int first = empty?.Length ?? Fallback();
        int second = missing?.Length ?? Fallback();
        return (first, second, calls);
    }
    #endregion

    #region Q68
    [Flags]
    private enum Permission
    {
        None = 0,
        Read = 1,
        Write = 2,
        Execute = 4
    }

    private static (bool All, bool Any) CheckPermissions()
    {
        Permission granted = Permission.Read | Permission.Write;
        Permission requested = Permission.Read | Permission.Execute;
        return (granted.HasFlag(requested), (granted & requested) != 0);
    }
    #endregion

    #region Q69
    private enum Mode { Fast = 1, Safe = 2 }

    private static (bool Parsed, bool Defined, int Value) ParseMode()
    {
        bool parsed = Enum.TryParse<Mode>("8", out var mode);
        return (parsed, Enum.IsDefined(mode), (int)mode);
    }
    #endregion

    #region Q70
    private static (int Count, int Capacity, int First, int Second) RenameTuple()
    {
        (int Count, int Capacity) original = (3, 10);
        (int Capacity, int Count) renamed = original;
        var (first, second) = renamed;
        return (renamed.Count, renamed.Capacity, first, second);
    }
    #endregion

    #region Q71
    private static void WriteThroughObjectArray()
    {
        string[] names = ["old"];
        object[] view = names;
        view[0] = 42;
    }
    #endregion

    #region Q72
    private static (int Cells, int Rows, int OuterLength, int LastRowLength) ArrayShapes()
    {
        int[,] grid = new int[2, 3];
        int[][] rows = [new int[2], new int[1]];
        return (grid.Length, grid.GetLength(0), rows.Length, rows[1].Length);
    }
    #endregion

    #region Q73
    private static (int Original, int Length, int First) SliceArray()
    {
        int[] original = [10, 20, 30, 40];
        int[] slice = original[1..^1];
        slice[0] = 99;
        return (original[1], slice.Length, slice[0]);
    }
    #endregion

    #region Q75
    private static string ReadRawText()
    {
        string text = """
            header
              "value"
            """;
        return text.ReplaceLineEndings("|");
    }
    #endregion

    #region Q76
    private static string FormatRawJson()
    {
        int count = 3;
        return $$"""{"count": {{count}}}""";
    }
    #endregion

    #region Q78
    private static (string For, string Foreach) CaptureLoops()
    {
        var forReads = new List<Func<int>>();
        for (int i = 0; i < 3; i++)
            forReads.Add(() => i);

        var eachReads = new List<Func<int>>();
        foreach (int value in new[] { 0, 1, 2 })
            eachReads.Add(() => value);

        return (string.Join(",", forReads.Select(read => read())),
            string.Join(",", eachReads.Select(read => read())));
    }
    #endregion

    #region Q80
    private static (string Display, string Wire) FormatAmount()
    {
        var previous = System.Globalization.CultureInfo.CurrentCulture;
        try
        {
            System.Globalization.CultureInfo.CurrentCulture =
                System.Globalization.CultureInfo.GetCultureInfo("fr-FR");
            decimal amount = 12.5m;
            string display = $"{amount:F1}";
            string wire = string.Create(
                System.Globalization.CultureInfo.InvariantCulture, $"{amount:F1}");
            return (display, wire);
        }
        finally
        {
            System.Globalization.CultureInfo.CurrentCulture = previous;
        }
    }
    #endregion
}
