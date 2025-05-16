// Test for found bug
addr jump_cache[10];
addr cache_pointer[] = jump_cache;
// here was 8bit instead of 16
addr X = succ(cache_pointer[]);

// Bug2: after EXTEND, not switching to 16bit
addr loc[];
byte L;
loc[] = L+1;