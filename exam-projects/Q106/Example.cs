// Q226 · 标志枚举的位组合（考试第 106 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    [Flags]
    private enum Access226 { None = 0, Read = 1, Write = 2, Execute = 4 }

    private static string Q226()
    {
        Access226 permissions = Access226.Read | Access226.Write;
        return $"{(int)permissions},{permissions.HasFlag(Access226.Write)},{permissions.HasFlag(Access226.Execute)}";
    }
}
