#region Q182
try { throw new FormatException(); }
catch (Exception) { Console.WriteLine("general"); }
catch (FormatException) { Console.WriteLine("specific"); }
#endregion
