// Q84 · 属性访问器的执行（考试第 146 题）


internal static partial class Question
{
    private sealed class Reading
    {
        private int reads;
        public int Value => ++reads;
    }
    private static (int First, int Second) ReadProperty()
    {
        var reading = new Reading();
        return (reading.Value, reading.Value);
    }
}
