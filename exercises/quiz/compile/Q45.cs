using System;
using System.Threading.Tasks;

await Parser.ReadAsync(new byte[4]);

#region Q45
public static class Parser
{
    public static async Task<int> ReadAsync(byte[] data)
    {
        Span<byte> header = data.AsSpan(0, 4);
        await Task.Yield();
        return header[0];
    }
}
#endregion
