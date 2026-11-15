#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>

void print_banner(void) {
    printf(
        "              ##########\n"
        "            ##..........####\n"
        "          ##................##\n"
        "        ##....................##\n"
        "      ##......##............####\n"
        "    ##........##..########..##..##\n"
        "    ##............##......##....##\n"
        "  ####............##......##......##\n"
        "  ##..............##......##........##\n"
        "##................##....####........##\n"
        "##..................##..##..........##\n"
        "##..................##..##..........##\n"
        "  ##..................##............##\n"
        "    ##................................##\n"
        "    ##....................................####\n"
        "    ####......................................##\n"
        "    ##..######..................................##\n"
        "    ##........##..................................##\n"
        "    ################################################\n"
        "\n"
        "Squawk squawk!\n"
        "*A very talkative parrot is perched in a cage in front of you.*\n"
        "*It seems very interested in you and repeats everything you say...*\n"
    );
}

__attribute__((noreturn))
void win(void) {
    char memory[128] = {0};
    FILE *fp = fopen("parrots_memory.txt", "r");
    printf("Parrot: Squawk! The cage is open!\n");
    printf("Parrot: To thank you, I'll tell you what the owner told me...\n");
    if (!fp) {
        goto forgot;
    }
    printf("Parrot: This is what the owner said: \n\n");
    while (fgets(memory, sizeof(memory), fp) != NULL) {
        fputs(memory, stdout);
    }
    if (ferror(fp)) {
        fclose(fp);
        goto forgot;
    }
    fclose(fp);
    exit(0);
forgot:
    puts("Parrot: ...Squawk? I can't remember what the owner said...\n");
    exit(1);
}

void challenge(void) {
    char message[64];
    char words[64];
    printf("Parrot: Squawk! Tell me something!\n");
    printf("You: ");
    if (!fgets(words, sizeof(words), stdin)) {
        printf("Parrot: ...Squawk? You didn't say anything...\n");
        exit(1);
    }
    printf("Parrot: Squawk! You said: ");
    printf(words);
    printf("Parrot: Oops... Was that supposed to be secret??\n");
    printf("Parrot: Whatever, you can leave a message for the owner!\n");
    printf("You: ");
    read(0, message, 256);
    printf("Parrot: Squawk! Message received! :)\n");
}

int main(void) {
    setbuf(stdin, NULL); setbuf(stdout, NULL); setbuf(stderr, NULL);
    print_banner();
    challenge();
    printf("Parrot: Squawk squawk! (Goodbye!)\n");
    return 0;
}