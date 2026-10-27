#region Q77
Fill(out int value, false);
Console.WriteLine(value);

static void Fill(out int value, bool ready)
{
    if (ready)
        value = 7;
}
#endregion
