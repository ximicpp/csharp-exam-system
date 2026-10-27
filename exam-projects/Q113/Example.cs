// Q233 · 抽象类的公共流程（考试第 113 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private abstract class Pipeline233
    {
        protected abstract int Step(int value);
        public int Run(int value) => Step(value) + 1;
    }
    private sealed class Double233 : Pipeline233
    {
        protected override int Step(int value) => value * 2;
    }

    private static string Q233()
    {
        Pipeline233 pipeline = new Double233();
        return pipeline.Run(3).ToString(CultureInfo.InvariantCulture);
    }
}
