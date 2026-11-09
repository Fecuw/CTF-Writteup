#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>

void corn_maze_exit() {
    char secret[128];
    const char *path = "/opt/ctf/chall1/secret.txt";
    FILE *f = fopen(path, "r");

    if (!f) { 
        printf("flag.txt missing \n"); 
        return; 
    }

    fgets(secret, sizeof secret, f);

    printf("\nYou've made it out of the maze! \n");
    printf("Secret value: %s", secret);
    printf("\nWell done! Use the secret value to unlock the next part of the challenge! \n");

}

void center_of_corn_maze() {
    printf("You're still stuck in the maze, try again! \n");
}

void vuln() {
    struct {
        char buf[64];
        void (*direction)();
    } s;

    s.direction = center_of_corn_maze;              
    printf("New sign direction: ");
    read(0, s.buf, 128);           
    s.direction();
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    printf(
        "You're stuck in a corn maze! All the signs are pointing you deeper into the maze, \ncan you redirect the sign to help you get out to POINT you in the right direction?"
    );
    printf("\n\nYou're somewhere in the maze... \n");
    vuln();
    return 0;
}