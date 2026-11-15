#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>

#include <unistd.h>
#include <err.h>

#define BUFFER_SIZE 0x20
#define MAX_NOTE    0x4

void win() {
    FILE *fp = fopen("flag.txt", "r");

    if (fp == NULL) {
        printf("flag.txt not found\n");
        return;
    }

    char flag[0x50];
    if (fgets(flag, sizeof(flag), fp) != NULL) {
        printf("%s\n", flag);
    }

    fclose(fp);
}

void normal_exit() {
    printf("bye\n");
}

typedef struct Note {
    char *data;
    int   is_used;
} Note;

Note notes[MAX_NOTE];

struct {
    void (*finalizer)(void);
    char  _pad[8];
} state __attribute__((aligned(0x10)));

void show_command() {
    printf("Command List : \n");
    printf("    1 : create note\n");
    printf("    2 : edit note\n");
    printf("    3 : delete note\n");
    printf("    4 : show note\n");
}

void create_note() {
    char *data = NULL;

    for (int i = 0; i < MAX_NOTE; i++) {
        if (!notes[i].is_used) {
            data = (char *)malloc(BUFFER_SIZE);
            notes[i].data = data;
            notes[i].is_used = true;
            break;
        }
    }

    if (data) {
        printf("creation success\n");
    } else {
        printf("creation failed\n");
    }
}

void edit_note() {
    int index;

    printf("index >> ");
    scanf("%d", &index);

    if (index < 0 || MAX_NOTE <= index) {
        printf("index is out of range\n");
        return;
    }

    printf("content >> ");
    read(STDIN_FILENO, notes[index].data, BUFFER_SIZE);
}

void delete_note() {
    int index;

    printf("index >> ");
    scanf("%d", &index);

    if (index < 0 || MAX_NOTE <= index) {
        printf("index is out of range\n");
        return;
    }

    if (!notes[index].is_used) {
        printf("already freed\n");
        return;
    }

    free(notes[index].data);
    notes[index].is_used = false;
}

void show_note() {
    for (int i = 0; i < MAX_NOTE; i++) {
        printf("notes[0x%x]\n", i);

        if (notes[i].data) {
            printf("%s\n",notes[i].data);
        } else {
            printf("    not allocated\n");
        }
    }
}

int main() {
    int input;
    int is_continued = 1;

    state.finalizer = normal_exit;

    while (is_continued) {
        show_command();

        printf("command >> ");
        scanf("%d", &input);

        switch (input) {
            case 1: create_note(); break;
            case 2: edit_note();   break;
            case 3: delete_note(); break;
            case 4: show_note();   break;
            default: is_continued = 0; break;
        }
    }

    state.finalizer();

    return 0;
}

__attribute__((constructor))
void init() {
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    alarm(60);
}
