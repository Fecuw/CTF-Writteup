#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include <unistd.h>
#include <err.h>

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

int main() {
    char password[8];
    char username[8];

    printf("username >> ");
    read(STDIN_FILENO, username, 8);
    
    if (!strcmp(username,"admin\n")) {
        printf("Admin cannot login.\n");
        printf("Bye.\n");
        return 0;
    }

    printf("password >> ");
    read(STDIN_FILENO, password, 0x10);

    printf("Hello %s.\n",username);

    if (!strcmp(username,"admin\n")) {
        printf("You are admin!\n");
        win();
    } else {
        printf("You are not admin.\n");
        printf("Bye.\n");
    }

    return 0;
}

__attribute__((constructor))
void init() {
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    alarm(60);
}