// Q238 · SDK 与目标框架各自决定什么（考试第 118 题）

internal static partial class Question
{
    private static string Observe() => typeof(Question).Assembly
        .GetCustomAttributes(typeof(System.Runtime.Versioning.TargetFrameworkAttribute), false)
        .Cast<System.Runtime.Versioning.TargetFrameworkAttribute>().Single().FrameworkName;

}
