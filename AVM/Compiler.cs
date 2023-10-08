using word = System.Byte;
using addr = System.UInt16;

namespace AVM
{
    public class Compiler
    {
        public static word[] ReadAndCompile(TextReader reader, TextWriter? dbgInfo = null)
        {
            if (reader == null)
                return Array.Empty<word>();
            string line;
            int lineNo = 0;
            var prg = new List<word>();

            addr address = VM.PROGRAM_BEGIN;

            Dictionary<string, addr> labels = new();
            Dictionary<addr, string> labelsToFill = new();

            Dictionary<string, int> constants = new ();
            Dictionary<string, UInt16> constants16 = new ();

            while ((line = reader.ReadLine()!) != null)
            {
                lineNo++;
                if (dbgInfo != null)
                { 
                    dbgInfo.WriteLine(string.Format("{0,6:#####}", address) + ": " + line);
                }

                line = line.Trim();

                // Strip comments
                if (line.Contains("//"))
                {
                    line = line.Substring(0, line.IndexOf("//")).Trim();
                }
                if (line.Contains(';'))
                {
                    line = line.Substring(0, line.IndexOf(';')).Trim();
                }
                if (string.IsNullOrEmpty(line)) continue;

                if (line.StartsWith("CONST "))
                {
                    var cTokens = line.Split(" ");
                    if (cTokens.Length != 3)
                        throw new Exception($"Invalid const at line {lineNo}, expected CONST NAME intValue");
                    var cOk = int.TryParse(cTokens[2], out int cValue);
                    if (!cOk)
                        throw new Exception($"Invalid const at line {lineNo}, expected CONST NAME intValue");
                    constants[cTokens[1]] = cValue;
                    continue;
                }
                if (line.StartsWith("CONST16 "))
                {
                    var cTokens = line.Split(" ");
                    if (cTokens.Length != 3)
                        throw new Exception($"Invalid const16 at line {lineNo}, expected CONST16 NAME intValue");
                    var cOk = UInt16.TryParse(cTokens[2], out UInt16 cValue);
                    if (!cOk)
                        throw new Exception($"Invalid const16 at line {lineNo}, expected CONST16 NAME intValue");
                    constants16[cTokens[1]] = cValue;
                    continue;
                }

                // Tokenize line while keeping quoted tokens together
                var tokens = line.Split('"')
                     .Select((element, index) => index % 2 == 0  // If even index
                                           ? element.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries)  // Split the item
                                           : new string[] { "\"" + element })  // Keep the entire item and keep quote in the beginning to mark ordinary string
                     .SelectMany(element => element).ToList();

                bool ok;
                foreach (var token in tokens)
                {
                    if (token.StartsWith("\""))
                    {
                        // Output ordinary string
                        var s = ParseEscapeCodes(token.Substring(1));
                        bool generateTerminator = true;
                        if (s.StartsWith("!"))
                        {
                            s = s.Substring(1);
                            generateTerminator = false;
                        }
                        foreach (var chr in s)
                        {
                            prg.Add((word)chr);
                            address++;
                        }
                        if (generateTerminator)
                        {
                            prg.Add(0);
                            address++;
                        }
                        continue;
                    }
                    if (token.StartsWith(":"))
                    {
                        // Label definition: collect it to fill later
                        var l = token.Substring(1);
                        if (labels.ContainsKey(l))
                            throw new Exception("Duplicate label " + l);
                        labels[l] = address;
                        continue;
                    }
                    if (token.StartsWith("@"))
                    {
                        // Label usage: collect it to fill later
                        labelsToFill[address] = token.Substring(1);
                        for (int ii = 0; ii < VM.ADDRESS_SIZE; ii++)
                        {
                            prg.Add(0);
                            address++;
                        }
                        continue;
                    }

                    var tokenU = token.ToUpper();
                    if (tokenU.StartsWith("INT."))
                    {
                        // Output interrupt code
                        ok = Enum.TryParse(tokenU.Substring(4), true, out InterruptCodes ic);
                        if (ok)
                        {
                            prg.Add((word)ic);
                            address++;
                            continue;
                        }
                        else
                        {
                            throw new Exception($"Invalid interrupt code {tokenU} at line {lineNo}");
                        }
                    }
                    if (tokenU.StartsWith("STD."))
                    {
                        // Output stdlib code
                        ok = Enum.TryParse(tokenU.Substring(4), true, out Stdlib ic);
                        if (ok)
                        {
                            prg.Add((word)ic);
                            address++;
                            continue;
                        }
                        else
                        {
                            throw new Exception($"Invalid stdlib code {tokenU} at line {lineNo}");
                        }
                    }
                    if (tokenU.StartsWith("CONST."))
                    {
                        if (!constants.ContainsKey(token.Substring(6)))
                            throw new Exception($"Unknown constant {tokenU} at line {lineNo}");
                        prg.Add((word)constants[token.Substring(6)]);
                        address++;
                        continue;
                    }
                    if (tokenU.StartsWith("CONST16."))
                    {
                        if (!constants16.ContainsKey(token.Substring(8)))
                            throw new Exception($"Unknown constant16 {tokenU} at line {lineNo}");
                        var bytes = BitConverter.GetBytes(constants16[token.Substring(8)]);
                        foreach (var b in bytes)
                        {
                            prg.Add(b);
                            address++;
                        }
                        continue;
                    }

                    if (token.StartsWith("#"))
                    {
                        // 16 bit int
                        ok = UInt16.TryParse(token.Substring(1), out UInt16 i16);
                        if (!ok)
                            throw new Exception($"Invalid bytes value {tokenU} at line {lineNo}");
                        var bytes = BitConverter.GetBytes(i16);
                        foreach (var b in bytes)
                        {
                            prg.Add(b);
                            address++;
                        }
                        continue;
                    }

                    ok = int.TryParse(token, out int i);
                    if (ok)
                    {
                        // Output ordinary integer 8bit
                        prg.Add((word)i);
                        address++;
                        continue;
                    }

                    // Output instruction:
                    ok = Enum.TryParse(tokenU, true, out I instruction);
                    if (ok)
                    {
                        prg.Add((word)instruction);
                        address++;
                        continue;
                    }

                    throw new Exception($"Invalid code {token} at line {lineNo}");
                }
            }

            foreach (var kvp in labelsToFill)
            {
                VM.write16(prg, kvp.Key - VM.PROGRAM_BEGIN, labels[kvp.Value]);
            }

            prg.Add((word)I.HALT);
            if (dbgInfo != null) dbgInfo.Flush();
            return prg.ToArray();
        }

        public static void WriteBinary(BinaryWriter bw, word[] program)
        { 
            foreach (var b in program)
                bw.Write(b);
        }

        public static void WriteBinary(string path, word[] program) {
            using (var f = File.Open(path, FileMode.Create))
            using (var bw = new BinaryWriter(f))
            WriteBinary(bw, program); 
        }

        public static word[] ReadBinary(BinaryReader br)
        {
            List<word> result = new List<word>();
            while (br.BaseStream.Position != br.BaseStream.Length)
            {
                //result.Add(br.ReadUInt16());
                result.Add(br.ReadByte());
            }
            return result.ToArray();
        }

        public static word[] ReadBinary(string path)
        {
            using (var f = File.Open(path, FileMode.Open))
            using (var br = new BinaryReader(f))
                return ReadBinary(br);
        }

        private static string ParseEscapeCodes(string str)
        {
            // Simple implementation for now:
            str = str.Replace("\\n", "\n");
            str = str.Replace("\\r", "\r");
            str = str.Replace("\\t", "\t");
            str = str.Replace("\\0", "\0");
            return str;
        }

        public static void Disassemble(word[] code, TextWriter txt) 
        {
            int address = 0;
            while (true) 
            {
                txt.Write(string.Format("{0,6:#####}", address));
                txt.Write(": ");
                var instr = (I)(code[address++]);
                txt.Write(instr.ToString() + " ");

                if (instr == I.INTERRUPT_HANDLER)
                {
                    txt.Write("InterruptCodes.");
                    txt.Write(((InterruptCodes)code[address++]).ToString() + " ");
                }
                else if (instr == I.SYSCALL)
                {
                    txt.Write("Stdlib.");
                    txt.Write(((Stdlib)code[address++]).ToString() + " ");
                }
                else if (instr == I.CALL || instr == I.JMP || instr == I.JT || instr == I.JF || instr == I.PUSH16 || instr == I.ADD16C || instr == I.MUL16C)
                {
                    addr val16bit = VM.read16(code, address);
                    address += 2;
                    txt.Write("#" + val16bit.ToString());
                }
                else
                {
                    var operands = VM.ProgramArgBytes(instr);
                    for (int j = 0; j < operands; j++)
                    {
                        txt.Write(code[address++].ToString() + " ");
                    }
                }
                txt.WriteLine();
                if (address >= code.Length)
                    break;
            }
            txt.Flush();
        }

    }
}
