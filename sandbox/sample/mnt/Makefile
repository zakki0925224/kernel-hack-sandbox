SRC_FILES := init.c
OBJ_FILES := $(SRC_FILES:.c=.o)
OUT_FILE := init

CC := gcc
CFLAGS := -Werror -g -O0

LDFLAGS := --static

$(OUT_FILE): $(OBJ_FILES)
	$(CC) $^ -o $@ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ_FILES) $(OUT_FILE)

all: $(OUT_FILE)

.PHONY: clean all