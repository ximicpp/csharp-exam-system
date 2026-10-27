// 故意不能编译：静态匿名函数不能捕获局部变量。
#region Q26
using System;

internal static class Program
{
    private static void Main()
    {
        int threshold = 10;
        Func<int, bool> accept = static value => value > threshold;
        Console.WriteLine(accept(20));
    }
}
#endregion
