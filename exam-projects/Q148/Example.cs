// Q88 · 可选参数与虚调用分两步（考试第 148 题）


internal static partial class Question
{
    private class BaseSender
    {
        public virtual int Send(int retries = 10) => retries;
    }
    private sealed class DerivedSender : BaseSender
    {
        public override int Send(int retries = 20) => retries;
    }
    private static (int ViaBase, int ViaDerived) OptionalDispatch()
    {
        var derived = new DerivedSender();
        BaseSender viaBase = derived;
        return (viaBase.Send(), derived.Send());
    }
}
