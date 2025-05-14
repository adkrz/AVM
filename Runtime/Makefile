# Compiler and flags
CXX := g++
CXXFLAGS := -std=c++20 -Wall -Wextra -O2

# Source files and output
SRCS := Compiler.cpp Runtime.cpp VM.cpp
OBJS := $(SRCS:.cpp=.o)
TARGET := compiler

# Default target
all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all clean