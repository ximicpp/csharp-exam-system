// Q57 · 锁与多字段一致性（考试第 142 题）
using System.Collections.Concurrent;

internal static partial class Question
{
    private sealed class Ledger
    {
        private readonly object gate = new();
        private int balance;
        private int version;

        public void DepositOne()
        {
            lock (gate)
            {
                balance++;
                version++;
            }
        }

        public (int Balance, int Version) Snapshot()
        {
            lock (gate) return (balance, version);
        }
    }
}
