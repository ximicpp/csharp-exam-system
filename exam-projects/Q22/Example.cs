// Q142 · 条件表达式的分支求值（考试第 22 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q142()
    {
        int calls = 0;
        int Next() => ++calls;
        bool fast = true;
        int chosen = fast ? Next() : Next() + 10;
        return $"{chosen},{calls}";
    }
}
