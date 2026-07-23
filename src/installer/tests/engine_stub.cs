using System;
using System.IO;

internal static class EngineStub
{
    private static int Main(string[] args)
    {
        string output = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "launch-record.txt");
        File.WriteAllLines(output, new[]
        {
            "cwd=" + Environment.CurrentDirectory,
            "command=" + Environment.CommandLine,
            "args=" + string.Join("|", args),
        });
        return 0;
    }
}
