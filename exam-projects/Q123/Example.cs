#region Q03
using System.Collections.Generic;

public struct Counter
{
    public int Value { get; set; }
}

public static class Program
{
    public static void Main()
    {
        var counters = new List<Counter> { new Counter { Value = 1 } };
        counters[0].Value++;
    }
}
#endregion
