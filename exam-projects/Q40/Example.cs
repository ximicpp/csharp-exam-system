#region Q160
using System.Collections.Generic;
foreach (int item in Read()) Console.WriteLine(item);
static IEnumerable<int> Read()
{
    try { yield return 1; }
    catch (InvalidOperationException) { yield break; }
}
#endregion
