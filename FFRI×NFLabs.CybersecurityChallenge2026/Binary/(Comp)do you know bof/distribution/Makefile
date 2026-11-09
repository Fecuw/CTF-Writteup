CC      := gcc
TARGET  := chall
SRC     := chall.c

CFLAGS  := -O0

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

clean:
	rm -f $(TARGET)