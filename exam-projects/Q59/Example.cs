// Q179 · 事件订阅与委托退订（考试第 59 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
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
}
