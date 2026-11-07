void vuln_func()
{
  char buf1[0x18];
  unsigned long secret = 0x1337;

  filename = "flag_1";

  print_stack(buf1);
  
  puts("[*] Please input data in 'buf1' ...");
  fgets(buf1, 0x70, stdin);
  check_buf(buf1);

  if (secret == 0xdeadbeef) {
    puts("[*] Congratulations! I will give you flag_1.");
    print_flag(filename);
    puts("[*] Let's submit flag and move on to the next challenge 'Beginners STACK #2'\n");
    print_stack(buf1);
  } else {
    puts("[*] check the stack frame! and overwirte 'secret' variable");
    print_stack(buf1);
  }
}
