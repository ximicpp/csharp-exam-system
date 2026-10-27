// Q187 · 包装读取器是否拥有底层流（考试第 67 题）
using System.Globalization;
using System.Text;
using System.Reflection;
using System.Linq.Expressions;

internal static partial class Question
{
    private static string Q187()
    {
        using MemoryStream stream = new([65]);
        string text;
        using (StreamReader reader = new(stream, Encoding.UTF8, false, 128, leaveOpen: true))
            text = reader.ReadToEnd();
        return $"{text},{stream.CanRead}";
    }
}
