// Q01 · 修改对象和替换调用方变量（考试第 121 题）
using System.Globalization;
using System.Numerics;
using System.Text;

internal static partial class Question
{
    private sealed class Session
    {
        public int Revision { get; set; }
    }

    private static void Update(Session session)
    {
        session.Revision = 2;
        session = new Session { Revision = 9 };
    }

    private static void Replace(ref Session session) =>
        session = new Session { Revision = 3 };

    private static (int AfterUpdate, int AfterReplace) PassReferences()
    {
        var session = new Session { Revision = 1 };
        Update(session);
        int first = session.Revision;
        Replace(ref session);
        return (first, session.Revision);
    }
}
