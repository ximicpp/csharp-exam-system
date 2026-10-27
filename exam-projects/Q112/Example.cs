// Q232 · 普通类的主构造参数（考试第 112 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
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
}
