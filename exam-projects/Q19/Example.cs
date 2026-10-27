// Q139 · Stack 的 Peek 与 Pop（考试第 19 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q139()
    {
        Stack<string> undo = new();
        undo.Push("edit");
        undo.Push("rename");
        string preview = undo.Peek();
        string removed = undo.Pop();
        return $"{preview},{removed},{undo.Count}";
    }
}
