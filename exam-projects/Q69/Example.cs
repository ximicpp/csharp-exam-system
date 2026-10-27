// Q189 · Stream.Read 的读取数量（考试第 69 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q189()
    {
        using MemoryStream stream = new([7, 8]);
        byte[] buffer = new byte[5];
        int count = stream.Read(buffer, 0, buffer.Length);
        return $"{count},{buffer[0]},{buffer[1]},{buffer[2]}";
    }
}
