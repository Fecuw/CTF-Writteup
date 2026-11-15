#include <stdio.h>
#include <stdlib.h>

void vuln(const char *secret) {
    char input[256];
    printf("Input: ");

    if (fgets(input, sizeof(input), stdin) == NULL)
        return;

    printf(input, secret);
    printf("\n");
}

int main(void) {
    char secret[256];

    FILE *fp = fopen("/opt/ctf/chall2/secret.txt", "r");
    if (fp == NULL) {
        perror("/opt/ctf/chall2/secret.txt");
        return 1;
    }

    if (fgets(secret, sizeof(secret), fp) == NULL) {a
        fclose(fp);
        return 1;
    }
    fclose(fp);

    vuln(secret);
    return 0;
}