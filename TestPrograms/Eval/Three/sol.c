#include <stdio.h>
#include <string.h>
#include <time.h>

char ENC[20] = {0x16, 0x0, 0x8, 0x10, 0x17, 0x4, 0xc, 0x1e, 0x11, 0xd, 0x17, 0x0, 0x0, 0x3a, 0x1, 0x55, 0xb, 0x0, 0x18, 0x00};

int check() {
    return 1 == 2;
}

int verify(char creds[10]) {
    int sum = 0;
    for (int i = 2; i < 10; i++) {
        sum += creds[i];
    }
    // First 2 bytes should be 0xde and 0xbb, name should be "samurai!"
    
    return (((unsigned char) creds[0]) + ((unsigned char) creds[1])  == 409) && (sum == 787);
}

void getFlag(char code[10]) {
    for (int i = 0; i < 19; i++) {
        ENC[i] = ENC[i] ^ (((unsigned char) code[0]) ^ ((unsigned char) code[1]));
    }
}

int main() {
    printf("Admin portal.\n");
    printf("Reading credentials...\n");
    
    char code[10];

    if (check()) {
        printf("Credentials read.\n");
    } else {
        printf("Credentials read fail.\n");
        printf("Using default values...\n");
        time_t curr = time(NULL);
        code[0] = 0xDE;
        code[1] = 0xBB;
        code[2] = 's';
        code[3] = 'a';
        code[4] = 'm';
        code[5] = 'u';
        code[6] = 'r';
        code[7] = 'a';
        code[8] = 'i';
        code[9] = '!';
        printf("[DEBUG] %x %x\n", (unsigned char) code[0], (unsigned char) code[1]);
    }


    if (verify(code)) {
        getFlag(code);
        printf("Correct! Flag is: %s\n", ENC);
    } else {
        printf("Failed.\n");
    }
    return 0;
}

