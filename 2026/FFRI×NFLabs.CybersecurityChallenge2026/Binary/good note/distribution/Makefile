CC      := gcc
TARGET  := good_note
SRC     := good_note.c

CFLAGS  := -no-pie

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

clean:
	rm -f $(TARGET)
