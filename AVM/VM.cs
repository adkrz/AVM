#define UNSAFE
using word = System.Byte;
using addr = System.UInt16;
using offs = System.Int16;
using System.Runtime.CompilerServices;

namespace AVM
{
#if UNSAFE
    public unsafe class VM
#else
    public class VM
#endif
    {
#if UNSAFE
        private word[] memoryBuffer = Array.Empty<word>();
        private addr[] registersBuffer = Array.Empty<addr>();
        private word* memory;
        private addr* registers;
#else
        private word[] memory = Array.Empty<word>();
        private addr[] registers = new addr[3];
#endif

        private const int IP_REGISTER = 0;
        private const int SP_REGISTER = 1;
        private const int FP_REGISTER = 2;
        public const int PROGRAM_BEGIN = 0;

        private const word WORD_SIZE = 1;  // size in array, not in bytes
        public const word ADDRESS_SIZE = 2;
        private int max_sp = 0;
        private ulong xic = 0; // executed instruction count
        Dictionary<InterruptCodes, addr> handlers = new(); // interrupt handlers
        private Random random = new Random();
        private string nvram_file = "";
        FileStream? nvram = null;
        private addr stackStartPos;



#region Lowest level instructions
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static addr read16(word[] list, int pos) => (addr)(list[pos + 1] * 256 + list[pos]); // BitConverter.ToUInt16(list, pos)
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static void write16(IList<word> list, int pos, addr value) { 
            list[pos] = (word)(value);
            list[pos+1] = (word)(value >> 8);
        }
        public static void write16(IList<word> list, int pos, offs value)
        {
            list[pos] = (word)(value);
            list[pos + 1] = (word)(value >> 8);
        }

#if UNSAFE
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static addr read16(word* list, int pos) => (addr)(list[pos + 1] * 256 + list[pos]); // BitConverter.ToUInt16(list, pos)
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static void write16(word* list, int pos, addr value)
        {
            list[pos] = (word)(value);
            list[pos + 1] = (word)(value >> 8);
        }
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static offs readoffs(word* list, int pos) => (offs)(list[pos + 1] * 256 + list[pos]); // BitConverter.ToUInt16(list, pos)
#endif

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        addr READ_REGISTER(int r) => registers[r];
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        void WRITE_REGISTER(int r, addr value) => registers[r] = value;
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        void ADD_TO_REGISTER(int r, int value) => registers[r] = (addr)(registers[r] + value);

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        void PUSH(word arg) { xic++; var sp_val = READ_REGISTER(SP_REGISTER); memory[sp_val] = arg; ADD_TO_REGISTER(SP_REGISTER, 1); if (sp_val + 1 > max_sp) max_sp = sp_val + 1; }
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        void PUSH_ADDR(addr arg) { xic++; var sp_val = READ_REGISTER(SP_REGISTER); write16(memory, sp_val, arg); ADD_TO_REGISTER(SP_REGISTER, ADDRESS_SIZE); if (sp_val + ADDRESS_SIZE > max_sp) max_sp = sp_val + ADDRESS_SIZE; }
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        void PUSHI(int arg) => PUSH((word)arg);
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        void PUSHI_ADDR(int arg) => PUSH_ADDR((addr)arg);
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        word POP() { xic++; var sp_val = READ_REGISTER(SP_REGISTER); var v = memory[sp_val - 1]; ADD_TO_REGISTER(SP_REGISTER, -1); return v; }
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        addr POP_ADDR() { xic++; var sp_val = READ_REGISTER(SP_REGISTER); var v = read16(memory, sp_val - ADDRESS_SIZE); ADD_TO_REGISTER(SP_REGISTER, -ADDRESS_SIZE); return v; }
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        word read_next_program_byte(ref word skip, int offset = 1)
        {
            var instr = READ_REGISTER(IP_REGISTER);
            var targ = memory[instr + offset];
            skip += WORD_SIZE;
            return targ;
        }
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        addr read_addr_from_program(ref word skip, int offset = 1)
        {
            var instr = READ_REGISTER(IP_REGISTER);
            var targ = read16(memory, instr + offset);
            skip += ADDRESS_SIZE;
            return targ;
        }
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        offs read_offs_from_program(ref word skip, int offset = 1)
        {
            var instr = READ_REGISTER(IP_REGISTER);
            var targ = readoffs(memory, instr + offset);
            skip += ADDRESS_SIZE;
            return targ;
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        void CALL(addr address, int offset = 0) // offset used in interrupts because we have no real "call" instruction in code
        {
            PUSHI_ADDR((READ_REGISTER(IP_REGISTER) + offset));
            PUSH_ADDR(READ_REGISTER(FP_REGISTER));
            WRITE_REGISTER(IP_REGISTER, address);
            WRITE_REGISTER(FP_REGISTER, READ_REGISTER(SP_REGISTER));
        }
#endregion

        /// <summary>
        /// Initializes the memory buffer, loads program to memory and sets initial register values.
        /// </summary>
        /// <param name="program"></param>
        /// <param name="memory_size"></param>
        /// <param name="nvram_file"></param>
        /// <param name="fillRemainingMemoryWithRandom">To catch bugs when memory is assumed to be zero but is not ;) </param>
        /// <param name="loadFrom">To play with PIC code</param>
        public void LoadProgram(word[] program, int memory_size=65535, string nvram_file="nvr.bin", bool fillRemainingMemoryWithRandom = true, addr loadFrom = PROGRAM_BEGIN)
        {
            if (memory_size < program.Length + 3) // plus registers
            {
                memory_size = program.Length + 3;
            }

#if UNSAFE
            memoryBuffer = GC.AllocateUninitializedArray<word>(memory_size, true);
            registersBuffer = GC.AllocateUninitializedArray<addr>(3, true);
            fixed (word* w = memoryBuffer)
                memory = w;
            fixed (addr* w = registersBuffer)
                registers = w;
#else
            memory = new word[memory_size];
            registers = new addr[3];
#endif


            WRITE_REGISTER(IP_REGISTER, loadFrom);
            for (int i = 0; i < program.Length; i++)
            {
                memory[i + loadFrom] = program[i];
            }

#if !UNSAFE
            if (fillRemainingMemoryWithRandom)
            {
                for (int i = program.Length; i < memory_size; i++)
                {
                    memory[i] = (word)random.Next(0, 255);
                }
            }
#endif
            stackStartPos = (addr)(program.Length + loadFrom);
            WRITE_REGISTER(SP_REGISTER, stackStartPos);
            WRITE_REGISTER(FP_REGISTER, stackStartPos);
            max_sp = READ_REGISTER(SP_REGISTER);
            xic = 0;
            handlers = new();
            this.nvram_file = nvram_file;
        }

        /// <summary>
        /// Execute application loaded by <see cref="LoadProgram(word[], int, string, bool)"/>
        /// </summary>
        public void RunProgram()
        {
            while (true)
            {
                var lastInstr = StepProgram();
                if (lastInstr == I.HALT)
                    break;
            }
        }

        /// <summary>
        /// Output simple total instruction count for each executed instruction
        /// </summary>
        /// <returns></returns>
        public Dictionary<I, ulong> ProfileProgram()
        {
            ulong cntr, cost;
            Dictionary<I, ulong> ret = new();
            while (true)
            {
                cntr = xic;
                var lastInstr = StepProgram();
                cost = xic - cntr;
                if (!ret.ContainsKey(lastInstr))
                    ret[lastInstr] = cost;
                else
                    ret[lastInstr] += cost;

                if (lastInstr == I.HALT)
                    break;
            }
            return ret.OrderByDescending(kvp => kvp.Value).ToDictionary(k => k.Key, k => k.Value);
        }

        /// <summary>
        /// Read how far the stack went during program execution
        /// </summary>
        public int MaxStackPointer => max_sp;
        /// <summary>
        /// Benchmark how many instructions were needed to complete execution
        /// </summary>
        public ulong ExecutedInstructionCount => xic;

        /// <summary>
        /// Executes one program step
        /// This is the place where all opcodes are implemented
        /// </summary>
        /// <returns></returns>
        public I StepProgram()
        {
            word skip;
            I instr;
            word arg;
            addr address;
            addr sp_value;
            int direction;
            int offset;

            instr = (I)memory[READ_REGISTER(IP_REGISTER)];
            skip = WORD_SIZE;
            xic++;
            try
            {
                switch (instr)
                {
                    case I.PUSH:
                        arg = read_next_program_byte(ref skip);
                        PUSH(arg);
                        break;
                    case I.PUSH16:
                        address = read_addr_from_program(ref skip);
                        PUSH_ADDR(address);
                        break;
                    case I.PUSH16_REL:
                        offset = read_offs_from_program(ref skip);
                        address = (addr)(READ_REGISTER(IP_REGISTER) + offset);
                        PUSH_ADDR(address);
                        break;
                    case I.PUSHN:
                        arg = read_next_program_byte(ref skip);
                        ADD_TO_REGISTER(SP_REGISTER, arg);
                        sp_value = READ_REGISTER(SP_REGISTER);
                        if (sp_value > max_sp) max_sp = sp_value;
                        break;
                    case I.PUSHN2:
                        ADD_TO_REGISTER(SP_REGISTER, POP());
                        sp_value = READ_REGISTER(SP_REGISTER);
                        if (sp_value > max_sp) max_sp = sp_value;
                        break;
                    case I.PUSH_NEXT_SP:
                        sp_value = READ_REGISTER(SP_REGISTER);
                        PUSHI_ADDR(sp_value + ADDRESS_SIZE);
                        break;
                    case I.PUSH_STACK_START:
                        PUSH_ADDR(stackStartPos);
                        break;
                    case I.POP:
                        POP();
                        break;
                    case I.POPN:
                        arg = read_next_program_byte(ref skip);
                        ADD_TO_REGISTER(SP_REGISTER, -arg);
                        break;
                    case I.POPN2:
                        ADD_TO_REGISTER(SP_REGISTER, -POP());
                        break;
                    case I.PUSH_REG:
                        arg = read_next_program_byte(ref skip);
                        PUSHI_ADDR(READ_REGISTER(arg));
                        break;
                    case I.POP_REG:
                        arg = read_next_program_byte(ref skip);
                        WRITE_REGISTER(arg, POP_ADDR());
                        break;
                    case I.ADD:
                        PUSHI((POP() + POP()));
                        break;
                    case I.ADD16:
                        PUSHI_ADDR((POP_ADDR() + POP_ADDR()));
                        break;
                    case I.ADD16C:
                        address = read_addr_from_program(ref skip);
                        PUSHI_ADDR((POP_ADDR() + address));
                        break;
                    case I.SUB:
                        PUSHI((POP() - POP()));
                        break;
                    case I.SUB2:
                        var arg1 = POP();
                        var arg2 = POP();
                        PUSHI((arg2-arg1));
                        break;
                    case I.SUB16:
                        PUSHI_ADDR((POP_ADDR() - POP_ADDR()));
                        break;
                    case I.SUB216:
                        var addr1 = POP_ADDR();
                        var addr2 = POP_ADDR();
                        PUSHI_ADDR((addr2-addr1));
                        break;
                    case I.DIV:
                        try
                        {
                            PUSHI((POP() / POP()));
                        }
                        catch (DivideByZeroException)
                        {
                            throw new InterruptException(InterruptCodes.DivisionByZeroError);
                        }
                        break;
                    case I.MOD:
                        try
                        {
                            PUSHI((POP() % POP()));
                        }
                        catch (DivideByZeroException)
                        {
                            throw new InterruptException(InterruptCodes.DivisionByZeroError);
                        }
                        break;
                    case I.MOD16:
                        try
                        {
                            PUSHI_ADDR((POP_ADDR() % POP_ADDR()));
                        }
                        catch (DivideByZeroException)
                        {
                            throw new InterruptException(InterruptCodes.DivisionByZeroError);
                        }
                        break;
                    case I.MUL:
                        PUSHI((POP() * POP()));
                        break;
                    case I.MUL16:
                        PUSHI_ADDR((POP_ADDR() * POP_ADDR()));
                        break;
                    case I.MUL16C:
                        address = read_addr_from_program(ref skip);
                        PUSHI_ADDR((POP_ADDR() * address));
                        break;

                    case I.EQ:
                        PUSHI(POP() == POP() ? 1 : 0);
                        break;
                    case I.NE:
                        PUSHI(POP() == POP() ? 0 : 1);
                        break;
                    case I.LESS:
                        PUSHI(POP() < POP() ? 1 : 0);
                        break;
                    case I.LESS_OR_EQ:
                        PUSHI(POP() <= POP() ? 1 : 0);
                        break;
                    case I.ZERO:
                        sp_value = READ_REGISTER(SP_REGISTER);
                        memory[sp_value - 1] = (word)(memory[sp_value - 1] == 0 ? 1 : 0);
                        break;

                    case I.EQ16:
                        PUSHI(POP_ADDR() == POP_ADDR() ? 1 : 0);
                        break;
                    case I.LESS16:
                        PUSHI(POP_ADDR() < POP_ADDR() ? 1 : 0);
                        break;
                    case I.LESS_OR_EQ16:
                        PUSHI(POP_ADDR() <= POP_ADDR() ? 1 : 0);
                        break;
                    case I.ZERO16:
                        PUSHI(POP_ADDR() == 0 ? 1 : 0);
                        break;

                    case I.AND:
                        PUSHI(POP() & POP());
                        break;
                    case I.OR:
                        PUSHI(POP() | POP());
                        break;
                    case I.XOR:
                        PUSHI(POP() ^ POP());
                        break;
                    case I.LSH:
                        PUSHI(POP() << POP());
                        break;
                    case I.RSH:
                        PUSHI(POP() >> POP());
                        break;
                    case I.FLIP:
                        PUSHI(~POP());
                        break;
                    case I.NOT:
                        sp_value = READ_REGISTER(SP_REGISTER);
                        memory[sp_value - 1] = (word)(memory[sp_value - 1] == 0 ? 1 : 0);
                        break;
                    case I.INC:
                        sp_value = READ_REGISTER(SP_REGISTER);
                        memory[sp_value - 1]++;
                        break;
                    case I.DEC:
                        sp_value = READ_REGISTER(SP_REGISTER);
                        memory[sp_value - 1]--;
                        break;
                    case I.INC16:
                        offset = READ_REGISTER(SP_REGISTER) - ADDRESS_SIZE;
                        write16(memory, offset, (addr)(read16(memory, offset) + 1));
                        break;
                    case I.DEC16:
                        offset = READ_REGISTER(SP_REGISTER) - ADDRESS_SIZE;
                        write16(memory, offset, (addr)(read16(memory, offset) - 1));
                        break;
                    case I.EXTEND:
                        PUSH_ADDR(POP());
                        break;
                    case I.JMP:
                        address = read_addr_from_program(ref skip);
                        WRITE_REGISTER(IP_REGISTER, address);
                        skip = 0;
                        break;
                    case I.JMP_REL:
                        offset = read_offs_from_program(ref skip);
                        ADD_TO_REGISTER(IP_REGISTER, offset);
                        skip = 0;
                        break;
                    case I.JF:
                        address = read_addr_from_program(ref skip);
                        if (POP() == 0)
                        {
                            WRITE_REGISTER(IP_REGISTER, address);
                            skip = 0;
                        }
                        break;
                    case I.JT:
                        address = read_addr_from_program(ref skip);
                        if (POP() != 0)
                        {
                            WRITE_REGISTER(IP_REGISTER, address);
                            skip = 0;
                        }
                        break;
                    case I.JF_REL:
                        offset = read_offs_from_program(ref skip);
                        if (POP() == 0)
                        {
                            ADD_TO_REGISTER(IP_REGISTER, offset);
                            skip = 0;
                        }
                        break;
                    case I.JT_REL:
                        offset = read_offs_from_program(ref skip);
                        if (POP() != 0)
                        {
                            ADD_TO_REGISTER(IP_REGISTER, offset);
                            skip = 0;
                        }
                        break;
                    case I.JMP2:
                        address = POP_ADDR();
                        WRITE_REGISTER(IP_REGISTER, address);
                        skip = 0;
                        break;
                    case I.JT2:
                        address = POP_ADDR();
                        if (POP() != 0)
                        {
                            WRITE_REGISTER(IP_REGISTER, address);
                            skip = 0;
                        }
                        break;
                    case I.JF2:
                        address = POP_ADDR();
                        if (POP() == 0)
                        {
                            WRITE_REGISTER(IP_REGISTER, address);
                            skip = 0;
                        }
                        break;
                    case I.CASE:
                        arg = read_next_program_byte(ref skip);
                        address = read_addr_from_program(ref skip, 2);
                        skip = 2 + ADDRESS_SIZE;
                        sp_value = READ_REGISTER(SP_REGISTER);
                        if (memory[sp_value - 1] == arg)
                        {
                            POP();
                            WRITE_REGISTER(IP_REGISTER, address);
                            skip = 0;
                        }
                        break;
                    case I.ELSE:
                        POP();
                        address = read_addr_from_program(ref skip);
                        WRITE_REGISTER(IP_REGISTER, address);
                        skip = 0;
                        break;
                    case I.CASE_REL:
                        arg = read_next_program_byte(ref skip);
                        offset = read_offs_from_program(ref skip, 2);
                        skip = 2 + ADDRESS_SIZE;
                        sp_value = READ_REGISTER(SP_REGISTER);
                        if (memory[sp_value - 1] == arg)
                        {
                            POP();
                            ADD_TO_REGISTER(IP_REGISTER, offset + 1);
                            skip = 0;
                        }
                        break;
                    case I.ELSE_REL:
                        POP();
                        offset = read_offs_from_program(ref skip);
                        ADD_TO_REGISTER(IP_REGISTER, offset);
                        skip = 0;
                        break;
                    case I.LOAD_GLOBAL:
                        address = POP_ADDR();
                        PUSH(memory[address]);
                        break;
                    case I.STORE_GLOBAL:
                        address = POP_ADDR();
                        arg = POP();
                        memory[address] = arg;
                        break;
                    case I.LOAD_GLOBAL16:
                        address = POP_ADDR();
                        PUSH_ADDR(read16(memory, address));
                        break;
                    case I.STORE_GLOBAL16:
                        address = POP_ADDR();
                        var val = POP_ADDR();
                        write16(memory, address, val);
                        break;
                    case I.LOAD:
                    case I.LOAD_LOCAL:
                    case I.LOAD_ARG:
                        arg = read_next_program_byte(ref skip);
                        direction = (instr == I.LOAD || instr == I.LOAD_ARG) ? -1 : 1;
                        offset = instr == I.LOAD_ARG ? 2 * ADDRESS_SIZE : 0;
                        PUSH(memory[READ_REGISTER(FP_REGISTER) + (arg + offset) * direction]);
                        break;
                    case I.LOAD_LOCAL16:
                    case I.LOAD_ARG16:
                        arg = read_next_program_byte(ref skip);
                        direction = (instr == I.LOAD_ARG16) ? -1 : 1;
                        offset = instr == I.LOAD_ARG16 ? 2 * ADDRESS_SIZE : 0;
                        PUSH_ADDR(read16(memory, READ_REGISTER(FP_REGISTER) + (arg + offset) * direction));
                        break;
                    case I.STORE:
                    case I.STORE_LOCAL:
                    case I.STORE_ARG:
                        arg = read_next_program_byte(ref skip);
                        direction = (instr == I.STORE || instr == I.STORE_ARG) ? -1 : 1;
                        offset = instr == I.STORE_ARG ? 2 * ADDRESS_SIZE : 0;
                        memory[READ_REGISTER(FP_REGISTER) + (arg + offset) * direction] = POP();
                        break;
                    case I.STORE_LOCAL16:
                    case I.STORE_ARG16:
                        arg = read_next_program_byte(ref skip);
                        direction = (instr == I.STORE_ARG16) ? -1 : 1;
                        offset = instr == I.STORE_ARG16 ? 2 * ADDRESS_SIZE : 0;
                        write16(memory, READ_REGISTER(FP_REGISTER) + (arg + offset) * direction, POP_ADDR());
                        break;
                    case I.LOAD_NVRAM:
                        address = POP_ADDR();
                        if (nvram == null)
                            nvram = OpenNvramFile();
                        nvram.Seek(address, SeekOrigin.Begin);
                        arg = (word)nvram.ReadByte();
                        PUSH(arg);
                        break;
                    case I.STORE_NVRAM:
                        address = POP_ADDR();
                        arg = POP();
                        if (nvram == null)
                            nvram = OpenNvramFile();
                        nvram.Seek(address, SeekOrigin.Begin);
                        nvram.WriteByte(arg);
                        break;
                    case I.CALL:
                    case I.CALL2:
                    case I.CALL_REL:
                        if (instr == I.CALL_REL)
                        {
                            offset = read_offs_from_program(ref skip);
                            address = (addr)(READ_REGISTER(IP_REGISTER) + offset);
                        }
                        else
                        {
                            address = instr == I.CALL ? read_addr_from_program(ref skip) : POP_ADDR();
                        }
                        CALL(address);
                        skip = 0;
                        break;
                    case I.RET:
                        WRITE_REGISTER(SP_REGISTER, READ_REGISTER(FP_REGISTER)); // clear stack after function execution
                        WRITE_REGISTER(FP_REGISTER, POP_ADDR());
                        address = POP_ADDR();
                        WRITE_REGISTER(IP_REGISTER, (addr)(address + ADDRESS_SIZE + 1)); // skip address of call and go to next instruction
                        skip = 0;
                        break;
                    case I.SWAP:
                        sp_value = READ_REGISTER(SP_REGISTER);
                        (memory[sp_value - 1], memory[sp_value - 2]) = (memory[sp_value - 2], memory[sp_value - 1]);
                        break;
                    case I.SWAP16:
                        sp_value = READ_REGISTER(SP_REGISTER);
                        var tmp = read16(memory, sp_value - ADDRESS_SIZE * 2);
                        write16(memory, sp_value - ADDRESS_SIZE * 2, read16(memory, sp_value - ADDRESS_SIZE));
                        write16(memory, sp_value - ADDRESS_SIZE, tmp);
                        break;
                    case I.DUP:
                        sp_value = READ_REGISTER(SP_REGISTER);
                        PUSH(memory[sp_value - 1]);
                        break;
                    case I.DUP16:
                        sp_value = READ_REGISTER(SP_REGISTER);
                        PUSH_ADDR(read16(memory, sp_value - ADDRESS_SIZE));
                        break;
                    case I.ROLL3:
                        var a = POP();
                        var b = POP();
                        var c = POP();
                        PUSH(a);
                        PUSH(c);
                        PUSH(b);
                        break;
                    case I.NEG:
                        PUSHI(-POP());
                        break;
                    case I.NOP:
                        break;
                    case I.DEBUGGER:
                        System.Diagnostics.Debugger.Break();
                        break;
                    case I.INTERRUPT_HANDLER:
                        arg = read_next_program_byte(ref skip);
                        address = read_addr_from_program(ref skip, 2);
                        skip = 2 + ADDRESS_SIZE;
                        if (address>0)
                            handlers[(InterruptCodes)arg] = address;
                        else
                            if (handlers.ContainsKey((InterruptCodes)arg))
                                handlers.Remove((InterruptCodes)arg);
                        break;
                    case I.SYSCALL:
                    case I.SYSCALL2:
                        arg = instr == I.SYSCALL ? read_next_program_byte(ref skip) : POP();
                        STDLIB(arg);
                        break;
                    case I.HALT:
                        if (nvram != null)
                        {
                            nvram.Close();
                            nvram = null;
                        }
                        return instr;
                    default:
                        throw new NotImplementedException($"Instruction not implemented: {instr}");
                }
            }
            catch (InterruptException ex)
            {
                if (handlers.ContainsKey(ex.Code))
                {
                    CALL(handlers[ex.Code], -ADDRESS_SIZE);
                    skip = 0;
                    xic++;
                }
                else
                {
                    Console.WriteLine("Program interrupted: " + ex.Code.ToString());
                    if (nvram != null)
                    {
                        nvram.Close();
                        nvram = null;
                    }
                    return I.HALT;
                }
            }
            ADD_TO_REGISTER(IP_REGISTER, skip);

            return instr;
        }

        /// <summary>
        /// My simple standard library implementation
        /// </summary>
        /// <param name="callNumber"></param>
        /// <exception cref="InterruptException"></exception>
        /// <exception cref="NotImplementedException"></exception>
        void STDLIB(int callNumber)
        {
            word arg;
            addr address;
            addr sp_value;

            void WriteStringToMemory(string str, int addr, int maxLen)
            {
                str = str.Substring(0, Math.Min(maxLen - 1, str.Length));
                for (int i = 0; i < str.Length; i++)
                    memory[address + i] = (word)str[i];
                memory[address + str.Length] = 0;
            }
            string ReadStringFromMemory(int addr)
            {
                var chars = new List<char>();
                var offs = 0;
                word chr;
                do
                {
                    chr = memory[address + offs++];
                    if (chr != 0)
                        chars.Add((char)chr);
                    else break;
                }
                while (chr != 0);
                return new string(chars.ToArray());
            }

            switch ((Stdlib)callNumber)
            {
                case Stdlib.PrintInt:
                    sp_value = READ_REGISTER(SP_REGISTER);
                    Console.Write(memory[sp_value - 1]);
                    break;
                case Stdlib.PrintInt16:
                    sp_value = READ_REGISTER(SP_REGISTER);
                    Console.Write(read16(memory, sp_value - ADDRESS_SIZE));
                    break;
                case Stdlib.PrintNewLine:
                    Console.WriteLine();
                    break;
                case Stdlib.PrintChar:
                    sp_value = READ_REGISTER(SP_REGISTER);
                    Console.Write((char)memory[sp_value - 1]);
                    break;
                case Stdlib.PrintCharPop:
                    Console.Write((char)POP());
                    break;
                case Stdlib.PrintString:
                    address = POP_ADDR();
                    word chr;
                    int offs = 0;
                    do
                    {
                        chr = memory[address + offs++];
                        Console.Write((char)chr);
                    }
                    while (chr != 0);
                    break;
                case Stdlib.ReadString:
                    var maxLen = POP();
                    address = POP_ADDR();
                    var line = Console.ReadLine();
                    WriteStringToMemory(line ?? "", address, maxLen);
                    break;
                case Stdlib.ReadKey:
                    if (Console.KeyAvailable)
                    {
                        var key = Console.ReadKey(true);
                        PUSHI(key.KeyChar);
                    }
                    else PUSH(0);
                    break;
                case Stdlib.SetConsoleCursorPosition:
                    arg = POP(); // top
                    var arg2 = POP(); // left
                    Console.SetCursorPosition(arg2, arg);
                    break;
                case Stdlib.ShowConsoleCursor:
                    arg = POP();
                    Console.CursorVisible = arg != 0;
                    break;
                case Stdlib.SetConsoleColors:
                    arg = POP();
                    arg2 = POP();
                    Console.ForegroundColor = VMColorToCsharpColor((Colors)arg);
                    Console.BackgroundColor = VMColorToCsharpColor((Colors)arg2);
                    break;
                case Stdlib.ConsoleClear:
                    Console.Clear();
                    break;
                case Stdlib.StringToInt:
                    address = POP_ADDR();
                    var str = ReadStringFromMemory(address);
                    var ok = word.TryParse(str, out word rslt);
                    if (ok)
                    {
                        PUSH(rslt);
                    }
                    else
                    {
                        throw new InterruptException(InterruptCodes.ParseError);
                    }
                    break;
                case Stdlib.IntToString:
                    var value = POP();
                    maxLen = POP();
                    address = POP_ADDR();
                    WriteStringToMemory(value.ToString(), address, maxLen);
                    break;
                case Stdlib.MemCpy:
                    maxLen = POP();
                    var targetAddress = POP_ADDR();
                    var srcAddress = POP_ADDR();
                    for (int i = 0; i < maxLen; i++)
                        memory[targetAddress + i] = memory[srcAddress + i];
                    break;
                case Stdlib.MemSet:
                    arg = POP();
                    sp_value = POP_ADDR(); // not sp value, simply reuse variable
                    address = POP_ADDR();
                    for (int i = 0; i < sp_value; i++)
                    {
                        memory[address + i] = arg;
                    }
                    break;
                case Stdlib.MemSwap:
                    var len = POP();
                    targetAddress = POP_ADDR();
                    srcAddress = POP_ADDR();
                    word tmp;
                    for (int i = 0; i < len; i++)
                    {
                        tmp = memory[targetAddress + i];
                        memory[targetAddress + i] = memory[srcAddress + i];
                        memory[srcAddress + i] = tmp;
                    }
                    break;
                case Stdlib.MemCmp:
                    len = POP();
                    targetAddress = POP_ADDR();
                    srcAddress = POP_ADDR();
                    int result = 0;
                    for (int i = 0; i < len; i++)
                    {
                        var a = memory[targetAddress + i];
                        var b = memory[srcAddress + i];
                        if (a != b)
                        {
                            result = srcAddress + i; break;
                        }
                    }
                    PUSHI(result);
                    break;
                case Stdlib.Strlen:
                    address = POP_ADDR();
                    offs = 0;
                    do
                    {
                        chr = memory[address + offs++];
                    }
                    while (chr != 0);
                    offs--;
                    PUSHI_ADDR(offs);
                    break;
                case Stdlib.Sleep:
                    address = POP_ADDR(); // not really an address :)
                    Thread.Sleep(address);
                    break;
                case Stdlib.GetRandomNumber:
                    arg = POP();
                    var min = POP();
                    PUSHI(random.Next(min, arg));
                    break;
                default:
                    throw new NotImplementedException($"Syscall not implemented: {callNumber}");
            }
        }

        /// <summary>
        /// Helper class to carry error numbers as C# exception
        /// </summary>
        private class InterruptException : System.Exception
        {
            public InterruptCodes Code { get; private set; }
            public InterruptException(InterruptCodes code) { Code = code; }
        }

        public word ReadMemory(int address)
        { 
            return memory[address];
        }

        public List<word> ReadMemory(int address, int length)
        {
            List<word> ret = new List<word>(length);
            for (int i = 0; i < length; i++)
            {
                ret.Add(memory[address + i]);
            }
            return ret;
        }

        /// <summary>
        /// You can put this to Watch in Visual Studio while debugging
        /// </summary>
        public List<word> StackFrameContents
        {
            get
            {
                var sf = StackFrameRange;
                return ReadMemory(sf.Item1, sf.Item2 - sf.Item1);
            }
        }

        /// <summary>
        /// Instruction pointers on call stack
        /// You can put this to Watch in Visual Studio while debugging, or in crash report.
        /// </summary>
        public List<addr> Backtrace
        {
            get
            {
                List<addr> bt = new List<addr>();
                var ip = READ_REGISTER(IP_REGISTER);
                var fp = READ_REGISTER(FP_REGISTER);
                bt.Add(ip);
                while (fp > stackStartPos)
                {
                    ip = read16(memory, fp - 2 * ADDRESS_SIZE);
                    fp = read16(memory, fp - ADDRESS_SIZE);
                    if (ip > 0)
                        bt.Add(ip);
                }
                
                return bt;
            }
        }

        private FileStream OpenNvramFile()
        {
            if (!File.Exists(nvram_file))
            {
                using (BinaryWriter binWriter = new BinaryWriter(File.Open(nvram_file, FileMode.Create)))
                {
                    for (int i = 0; i < addr.MaxValue; i++)
                    {
                        binWriter.Write((word)0);
                    }
                }
            }
            return File.Open(nvram_file, FileMode.Open, FileAccess.ReadWrite, FileShare.Read);
        }

        public addr InstructionPointer => READ_REGISTER(IP_REGISTER);

        public (addr, addr) StackFrameRange => (READ_REGISTER(FP_REGISTER), READ_REGISTER(SP_REGISTER));

        private ConsoleColor VMColorToCsharpColor(Colors col) => col switch
        {
            Colors.Black or Colors.BrightBlack => ConsoleColor.Black,
            Colors.Red => ConsoleColor.DarkRed,
            Colors.BrightRed => ConsoleColor.Red,
            Colors.Green => ConsoleColor.DarkGreen,
            Colors.BrightGreen => ConsoleColor.Green,
            Colors.Yellow => ConsoleColor.DarkYellow,
            Colors.BrightYellow => ConsoleColor.Yellow,
            Colors.Blue => ConsoleColor.DarkBlue,
            Colors.BrightBlue => ConsoleColor.Blue,
            Colors.Magenta => ConsoleColor.DarkMagenta,
            Colors.BrightMagenta => ConsoleColor.Magenta,
            Colors.Cyan => ConsoleColor.DarkCyan,
            Colors.BrightCyan => ConsoleColor.Cyan,
            Colors.Gray => ConsoleColor.DarkGray,
            Colors.BrightGray => ConsoleColor.Gray,
            _ => ConsoleColor.White,
        };

        /// <summary>
        /// How many args bytes from program each instruction needs
        /// </summary>
        /// <param name="i"></param>
        /// <returns></returns>
        public static int ProgramArgBytes(I i) => i switch { 
            I.PUSH or I.PUSHN or I.POPN or I.PUSH_REG or I.POP_REG => 1,
            I.JMP or I.JT or I.JF or I.CALL => 2,
            I.LOAD or I.STORE or I.LOAD_ARG or I.STORE_ARG or I.LOAD_LOCAL or I.STORE_LOCAL or I.LOAD_LOCAL16 or I.STORE_LOCAL16  or I.LOAD_ARG16 or I.STORE_ARG16 => 1,
            I.INTERRUPT_HANDLER => 1,
            I.SYSCALL => 1,
            I.PUSH16 => 2,
            I.ADD16C or I.MUL16C => 2,
            _ => 0
        };
    }
}
