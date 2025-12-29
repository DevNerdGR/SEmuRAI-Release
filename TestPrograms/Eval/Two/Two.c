#include <stdio.h>
#include <string.h>

int MAGIC_CODE = 0xDE;

char ENC[] = {0xa7, 0xb1, 0xb9, 0xa1, 0xa6, 0xb5, 0xbd, 0xaf, 0xb8, 0xb1, 0xa2, 0xb1, 0xb8, 0x8b, 0xe6, 0x8b, 0xb0, 0xbb, 0xba, 0xb1, 0xb1, 0xb1, 0xa9, 0x00};

int verify(int code) {
    // Valid code is 212
    return (code ^ MAGIC_CODE) == 10;
}

void decode(int code) {
    size_t len = strlen(ENC);

    for (int i = 0; i < len; i++) {
        ENC[i] = ENC[i] ^ code;
    }
}

int main() {
    printf("Admin portal.\n");
    int ID = 0;
    printf("Logged in as user %d\n", ID);
    
    if (verify(ID)) {
        decode(ID);
        printf("Flag: %s\n", ENC);
    } else {
        printf("Not authorized.\n");
    }
    return 0;
}
