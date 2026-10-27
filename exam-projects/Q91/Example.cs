// Q211 · 本机缓冲区的释放契约（考试第 91 题）

internal static partial class Question
{
    private static int releases;
    private static IntPtr AllocateBuffer() => System.Runtime.InteropServices.Marshal.AllocHGlobal(sizeof(int));
    private static void ReleaseBuffer(IntPtr address)
    {
        System.Runtime.InteropServices.Marshal.FreeHGlobal(address);
        releases++;
    }
    private sealed class BufferHandle : System.Runtime.InteropServices.SafeHandle
    {
        public BufferHandle() : base(IntPtr.Zero, true) => SetHandle(AllocateBuffer());
        public override bool IsInvalid => handle == IntPtr.Zero;
        protected override bool ReleaseHandle() { ReleaseBuffer(handle); return true; }
    }
    private static (int Value, int Releases) Observe()
    {
        int value;
        using (var buffer = new BufferHandle())
        {
            System.Runtime.InteropServices.Marshal.WriteInt32(buffer.DangerousGetHandle(), 7);
            value = System.Runtime.InteropServices.Marshal.ReadInt32(buffer.DangerousGetHandle());
        }
        return (value, releases);
    }

}
