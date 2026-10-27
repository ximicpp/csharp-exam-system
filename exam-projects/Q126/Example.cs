#region Q09
using System;

public interface IRevisioned
{
    int Revision { get; }
}

public sealed record Document(int Revision) : IRevisioned;

public static class Program
{
    public static bool IsNewer<T>(T left, T right) => left.Revision > right.Revision;

    public static void Main() =>
        Console.WriteLine(IsNewer(new Document(2), new Document(1)));
}
#endregion
