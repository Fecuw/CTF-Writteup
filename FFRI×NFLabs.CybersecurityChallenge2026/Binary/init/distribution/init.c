#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include<stdint.h>

/* 標準入力バッファのクリア */
void clear(){
  int c;
  while((c = getchar()) != '\n' && c != EOF);
}

void print_flag(){
  FILE* f = fopen("flag.txt", "r");
  if(!f){
    fprintf(stderr, "[Error] Cannot open flag.txt\n");
    exit(1);
  }
  char Flag[64];
  memset(Flag, 0, sizeof(Flag));
  fread(Flag, 1, 64, f); 
  printf("\n====================\n");
  printf("Congratulations!!\n\n");
  printf("%s",Flag);
  printf("====================\n");
}

void check(int32_t input_num){
  struct Data {
    int32_t alfa;
    unsigned char bravo[4];
    int32_t charlie;
    unsigned char delta;
    int32_t echo;
    unsigned char foxtrot[4];
  };

  struct Data data;

  data.alfa = 1;
  strcpy(data.bravo,"abcd");
  data.charlie = 2;
  data.delta = 'a';
  data.echo = 1440;
  data.foxtrot[0] = 0xab;
  if (input_num <= 100) {
    data.foxtrot[1] = 0x00;
  }
  data.foxtrot[2] = 0xcd;
  data.foxtrot[3] = 0xef;

  if(((data.foxtrot[1] & 0xfc) == 0xc8) && (data.foxtrot[1] != 0xc8)){
    print_flag();
  }
}

int32_t input(){
  unsigned char name[8];
  int32_t fav_num = -1;
  memset(name, 0, sizeof(name));
  printf("Input your name: ");
  scanf("%7s",name);
  clear();
  printf("Input your favorite number: ");
  scanf("%d",&fav_num);
  clear();
  printf("hello, %s !!!\nYour favorite number is %d !!!\n", name, fav_num);
  return fav_num;
}

int main(){
  setvbuf(stdin, NULL, _IONBF, 0);
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stderr, NULL, _IONBF, 0);

  int32_t num = -1;
  num = input();
  check(num);
  return 0;
}
